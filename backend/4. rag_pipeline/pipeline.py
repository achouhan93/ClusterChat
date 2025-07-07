import json
import logging
import re
from typing import Any, Dict, List, Tuple

from torch import cuda
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from langchain.prompts import PromptTemplate

import utils
from tasks.rag_components import rag_loader, rag_prompt, rag_chatmodel

log = logging.getLogger(__name__)
CONFIG = utils.load_config_from_env()


class Processor:
    """
    Processor class for managing the text retrieval and response generation
    pipeline using OpenSearch, SentenceTransformer embeddings, and LLMs.
    """

    def __init__(
        self,
        opensearch_connection: Any,
        embedding_os_index: str,
        embedding_model: str,
        model_config: Dict[str, Any],
    ) -> None:
        """
        Initializes the Processor.

        Args:
            opensearch_connection (Any): Active OpenSearch connection.
            embedding_os_index (str): Index name in OpenSearch to retrieve embeddings.
            embedding_model (str): Name or path of the embedding model.
            model_config (Dict[str, Any]): Configuration for the language model.
        """
        self.os_connection = opensearch_connection
        self.embeddings_os_index_name = embedding_os_index
        self.device = f"cuda:{cuda.current_device()}" if cuda.is_available() else "cpu"

        self.embed_model = SentenceTransformer(
            model_name_or_path=embedding_model,
            trust_remote_code=True,
            device=self.device,
        )

        self.vector_store = rag_loader.RagLoader().get_opensearch_index(
            self.embed_model, self.embeddings_os_index_name
        )

        self.model_config = model_config
        self.prompt = rag_prompt.RagPrompt().prompt_template()

        self.chat_model = rag_chatmodel.RagChat(
            vector_store=self.vector_store,
            prompt_object=self.prompt,
            prompt_vars=["context", "question"],
            embedding_model=self.embed_model,
            model_config=self.model_config,
        )
        
        self.llm = self.chat_model.llm
        
        # Define the OpenSearch index names
        self.cluster_information_index = CONFIG[
            "CLUSTER_CHAT_CLUSTER_INFORMATION_INDEX"
        ]

        self._init_prompt_chains()

    def _init_prompt_chains(self) -> None:
        """Initializes LangChain prompt chains for parsing and answering."""

        #!! Prompt when OpenAI is used
        parse_query_template = """
        You are an assistant that parses user queries into structured intents for querying a corpus.

        Given the following user query, extract the intent and relevant parameters in JSON format ONLY. Do not include any additional text or comments.

        Supported intents:
        1. list_topics_in_cluster
        2. list_questions_in_cluster
        3. get_corpus_info

        User Query: "{user_query}"

        Output JSON ONLY in the following format without any additional text:
        {{
            "intent": "<intent_name>",
            "parameters": {{
                // parameters based on intent
            }}
        }}
        """

        #! Prompt when Model from HuggingFace is Used
        # parse_query_template = """
        # You are an assistant that parses user queries into structured intents for querying a corpus.

        # Given the following user query, extract the intent and relevant parameters in JSON format ONLY. Do not include any additional text or comments.

        # Supported intents and their expected parameters:

        # 1. **list_topics_in_cluster**
        # - **Description:** Lists all topics within a specified cluster.
        # - **Parameters:**
        #     - **cluster** *(string)*: The name of the cluster from which to list topics.

        # 2. **list_questions_in_cluster**
        # - **Description:** Lists all questions associated with a specified cluster.
        # - **Parameters:**
        #     - **cluster** *(string)*: The name of the cluster from which to list questions.

        # 3. **get_corpus_info**
        # - **Description:** Retrieves general information about the corpus, such as statistics or metadata.
        # - **Parameters:**
        #     - **none**: This intent does not require any parameters.

        # **User Query:** "{user_query}"

        # **Output JSON ONLY in the following format without any additional text:**
        # {{
        #     "intent": "<intent_name>",
        #     "parameters": {{}}
        # }}
        # """

        parse_query_prompt = PromptTemplate(
            input_variables=["user_query"], template=parse_query_template
        )
        self.parse_query_chain = parse_query_prompt | self.llm

        # Initialize LangChain LLMChain for generating answers
        generate_answer_template = """
        You are an assistant that provides answers based on the retrieved data from a corpus.
        
        Given the user query and the retrieved data, generate a concise and informative answer.
        
        User Query: "{user_query}"
        
        Retrieved Data:
        {retrieved_data}
        
        Answer:
        """
        generate_answer_prompt = PromptTemplate(
            input_variables=["user_query", "retrieved_data"],
            template=generate_answer_template,
        )
        self.generate_answer_chain = generate_answer_prompt | self.llm

    def parse_user_query(self, user_query: str) -> Dict[str, Any]:
        """
        Uses LLM to parse user query into structured intent and parameters.

        Args:
            user_query (str): The user's input question.

        Returns:
            Dict[str, Any]: Parsed JSON with intent and parameters.
        """
        response = self.parse_query_chain.invoke({"user_query": user_query})
        try:
            # Use regex to find JSON within the response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in the response.")

            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError:
            raise ValueError(
                f"Failed to parse the user query. LLM Response: {response}"
            )

    def build_opensearch_query(
        self, intent: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Builds OpenSearch query from the parsed intent and parameters.

        Returns:
            Dict[str, Any]: The query body for OpenSearch.
        """
        if intent == "list_topics_in_cluster":
            cluster_label = parameters.get("cluster_labels")
            if not cluster_label:
                raise ValueError(
                    "Parameter 'cluster_label' is required for listing topics in a cluster."
                )
            query = {"bool": {"must": [{"match_phrase": {"label": cluster_label}}]}}
            return {"query": query, "_source": ["label", "description", "topic_words"]}

        elif intent == "list_questions_in_cluster":
            cluster_label = parameters.get("cluster_labels")
            if not cluster_label:
                raise ValueError(
                    "Parameter 'cluster_label' is required for listing questions in a cluster."
                )
            # Assuming 'questions' are stored in 'description' or another field; adjust as needed
            query = {"bool": {"must": [{"match_phrase": {"label": cluster_label}}]}}
            return {
                "query": query,
                "_source": ["description", "topic_words"],
            }  # Adjust the field as per your mapping

        elif intent == "get_corpus_info":
            # For general corpus information, you might aggregate data or fetch specific fields
            #! This hardcoding can be replaced by computing the max depth in clusterinformation index and then subtract 4 inorder to get top hierarchy cluster information
            return {
                "query": {"bool": {"filter": {"range": {"depth": {"gte": 35}}}}}, 
                "size": 10000,
                "_source": ["label", "description"],
            }

        else:
            raise ValueError(f"Unsupported intent: {intent}")

    def execute_opensearch_query(self, query: Dict[str, Any]) -> Any:
        """
        Executes an OpenSearch query.

        Returns:
            OpenSearch response as a dict.
        """
        try:
            response = self.os_connection.search(
                index=self.cluster_information_index, body=query
            )
            return response
        except Exception as e:
            log.error(f"OpenSearch query failed: {e}")
            raise e

    def generate_answer(self, user_query: str, retrieved_data: str) -> str:
        """
        Uses LLM to generate an answer from user query and retrieved corpus data.

        Returns:
            str: Generated natural language response.
        """
        response = self.generate_answer_chain.invoke(
            {"user_query": user_query, "retrieved_data": retrieved_data}
        )
        return response.strip()

    def process_corpus_specific_request(
        self, question: str, cluster_information: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Handles corpus-specific questions by aggregating cluster information and generating an answer.

        :param question: The user's question.
        :param cluster_information: List of cluster labels provided by the user. Can be empty.
        :return: A tuple containing the answer and list of source cluster IDs.
        """
        try:
            if cluster_information:
                should_clauses = [
                    {"match_phrase": {"label": phrase}}
                    for phrase in cluster_information
                ]

                query_body = {
                    "query": {
                        "bool": {"should": should_clauses, "minimum_should_match": 1}
                    },
                    "_source": ["cluster_id", "label", "description", "topic_words"],
                }
                log.info(
                    f"Executing OpenSearch query with cluster labels: {cluster_information}"
                )
            else:
                # If cluster_information is empty, parse the question to extract cluster labels
                parsed_query = self.parse_user_query(question)
                intent = parsed_query.get("intent")
                parameters = parsed_query.get("parameters", {})

                if intent in ["get_corpus_info"]:
                    query_body = self.build_opensearch_query(intent, {})
                    log.info(f"Executing OpenSearch query with Corpus information")
                elif intent not in [
                    "list_topics_in_cluster",
                    "list_questions_in_cluster",
                    "get_corpus_info",
                ]:
                    raise ValueError(
                        f"Unsupported intent '{intent}' for corpus-specific query."
                    )
                else:
                    cluster_labels = parameters.get("cluster")
                    if not cluster_labels:
                        raise ValueError(
                            "No cluster labels extracted from the question."
                        )

                    query_body = self.build_opensearch_query(
                        intent, {"cluster_labels": cluster_labels}
                    )
                    log.info(
                        f"Executing OpenSearch query with parsed cluster labels: {cluster_labels}"
                    )

            # Execute the OpenSearch query
            response = self.execute_opensearch_query(query_body)
            hits = response["hits"]["hits"]

            if not hits:
                raise ValueError("No relevant clusters found for the given query.")

            # Extract relevant information from hits
            clusters = []
            sources = []

            for hit in hits:
                source = hit["_source"]
                cluster_id = hit.get("_id", "")
                label = source.get("label", "")
                description = source.get("description", "No description available.")
                topic_words = source.get("topic_words", [])
                clusters.append(
                    {
                        "label": label,
                        "description": description,
                        "topic_words": topic_words,
                    }
                )
                sources.append(cluster_id)

            # Aggregate retrieved information
            retrieved_info = "\n".join(
                [json.dumps(cluster, indent=2) for cluster in clusters]
            )

            # Generate the answer using LLM
            answer = self.generate_answer(question, retrieved_info)
            cleaned_answer = answer.strip()

            return cleaned_answer, sources

        except ValueError as ve:
            log.error(f"ValueError: {ve}")
            raise ve
        except Exception as e:
            log.error(f"Error processing corpus-specific request: {e}")
            raise RuntimeError(f"Error processing corpus-specific request: {e}")

    def process_api_request(
        self, question: str, document_ids: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Process an API request to generate an answer based on the question, question type, and document IDs.

        :param question: The user's question as a string.
        :param question_type: Type of question, 'corpus-based' or 'document-specific'.
        :param document_ids: List of document IDs to restrict the search to. If empty, use the whole corpus.
        :return: A tuple (answer, sources)
        """
        try:
            context, retrieved_ids = self.chat_model.vector_augment_prompt_api(
                query=question, top_k_value=10, document_ids=document_ids
            )

            # Generate the answer
            answer = self.chat_model.llm_chain.invoke(
                {"context": context, "question": question}
            )
            cleaned_answer = answer.strip()
            return cleaned_answer, retrieved_ids

        except Exception as e:
            log.error(f"Error processing API request: {e}")
            raise RuntimeError(f"Error processing API request: {e}")

    def encode_text(self, text: str) -> List[float]:
        """
        Encodes a given text using the embedding model.

        Args:
            text (str): Input text to encode.

        Returns:
            List[float]: Vector embedding.
        """
        return self.embed_model.encode(text).tolist()
