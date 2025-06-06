import logging
from typing import List, Tuple, Dict, Any

import utils
from torch import cuda
from tqdm import tqdm
from transformers import AutoTokenizer
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate

# When OpenAI model is used
from langchain_openai import OpenAI

CONFIG: Dict[str, Any] = utils.loadConfigFromEnv()
logger = logging.getLogger(__name__)


class Document:
    """
    A lightweight representation of a document with content and metadata.
    """

    def __init__(self, page_content: str, metadata: Dict[str, Any]) -> None:
        self.page_content = page_content
        self.metadata = metadata


class RagChat:
    """
    A class for Retrieval-Augmented Generation (RAG) chat using a vector store and language model.
    """

    def __init__(
        self,
        vector_store: Any,
        prompt_object: str,
        prompt_vars: List[str],
        embedding_model: Any,
        model_config: Dict[str, Any],
    ) -> None:
        """
        Initializes the RAG chat pipeline with LLM, tokenizer, and vector index.

        Args:
            vector_store (Any): Vector store client (e.g., OpenSearch).
            prompt_object (str): Prompt template string.
            prompt_vars (List[str]): Variables used in the prompt template.
            embedding_model (Any): Sentence embedding model.
            model_config (Dict[str, Any]): Configuration for the generation model.
        """
        self.device = "cuda" if cuda.is_available() else "cpu"
        self.index = vector_store
        self.embed_model = embedding_model
        self.prompt = prompt_object

        self.max_context = model_config.get("n_ctx", 4096)  # Maximum number of tokens
        self.max_generated_token = model_config.get("max_tokens", 200)

        self.model_id = model_config["huggingface_model"]
        self.hf_auth = CONFIG["HUGGINGFACE_AUTH_KEY"]
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

        self.llm = HuggingFaceEndpoint(
            repo_id=self.model_id,
            max_new_tokens=self.max_generated_token,
            temperature=model_config.get("temperature", 0.1),
            huggingfacehub_api_token=self.hf_auth,
            repetition_penalty=model_config.get("repetition_penalty", 1.2),
            stop_sequences=model_config.get("stop_sequences", ["</s>"]),
        )

        self.llama_prompt = PromptTemplate(
            template=self.prompt, input_variables=prompt_vars
        )
        self.llm_chain = self.llama_prompt | self.llm
        logger.info("RagChat initialized successfully.")

    def process_results(
        self, results: List[Tuple[Document, float]], max_tokens_for_knowledge: int
    ) -> Tuple[str, List[str]]:
        """
        Processes retrieved documents into a knowledge string within a token limit.

        Args:
            results (List[Tuple[Document, float]]): List of (document, score) pairs from retrieval.
            max_tokens_for_knowledge (int): Maximum number of tokens to be used for knowledge input.

        Returns:
            Tuple[str, List[str]]: Concatenated knowledge string and top document IDs (up to 5).
        """
        source_knowledge = ""
        retrieved_ids: List[str] = []

        for result, _ in tqdm(results, desc="Processing search results", leave=False):
            text = result.page_content
            updated_knowledge = (
                source_knowledge + ("\n" if source_knowledge else "") + text
            )
            new_tokens_num = len(self.tokenizer.encode(updated_knowledge))

            if new_tokens_num > max_tokens_for_knowledge:
                logger.warning("Token limit reached, stopping knowledge accumulation.")
                break

            source_knowledge = updated_knowledge
            retrieved_ids.append(result.metadata["documentID"])

        unique_ids = list(set(retrieved_ids))
        return source_knowledge, unique_ids[:5]

    def vector_augment_prompt_api(
        self, query: str, top_k_value: int, document_ids: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Augments a prompt with retrieved knowledge from a vector index.

        Args:
            query (str): The user query.
            top_k_value (int): Number of top similar documents to retrieve.
            document_ids (List[str]): Allowed document IDs for filtering retrieval.

        Returns:
            Tuple[str, List[str]]: Augmented knowledge and document IDs used.
        """
        try:
            # Encoding the query
            embed_query = self.embed_model.encode(
                [query], show_progress_bar=False
            ).tolist()

            # Compute available space for knowledge based on prompt and query
            max_tokens_for_knowledge = (
                self.max_context
                - len(self.tokenizer.encode(query))
                - len(self.tokenizer.encode(self.prompt))
                - 100
            )

            # Prepare the search query
            search_query = {
                "size": top_k_value,
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "filter": [{"terms": {"documentID": document_ids}}]
                            }
                        },
                        "script": {
                            "source": 'cosineSimilarity(params.query_value, doc["pubmed_bert_vector"]) + 1.0',
                            "params": {"query_value": embed_query[0]},
                        },
                    }
                },
                "_source": ["abstract_chunk", "documentID"],
            }

            results = self.index.client.search(
                index=CONFIG["CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_SENTENCE"],
                body=search_query,
                request_timeout=10,
            )

            # Process results
            updated_results = [
                (
                    Document(
                        page_content=hit["_source"]["abstract_chunk"],
                        metadata=hit["_source"],
                    ),
                    hit["_score"],
                )
                for hit in results["hits"]["hits"]
            ]

            source_knowledge, retrieved_ids = self.process_results(
                updated_results, max_tokens_for_knowledge
            )

            return source_knowledge, retrieved_ids

        except Exception as e:
            logger.error(f"Failed to augment prompt: {e}")
            raise
