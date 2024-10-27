import logging
from torch import cuda
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from tqdm import tqdm
import json
import utils
from transformers import AutoTokenizer

CONFIG = utils.loadConfigFromEnv()
log = logging.getLogger(__name__)


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


class ragChat:
    def __init__(
        self,
        vector_store,
        prompt_object,
        prompt_vars,
        embedding_model,
        model_config
    ) -> None:
        """
        Initializes a ragChat object with specified configurations for text retrieval and generation.
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
            stop_sequences=model_config.get("stop_sequences", ["</s>"])
        )

        self.llama_prompt = PromptTemplate(
            template=self.prompt, input_variables=prompt_vars
        )
        self.llm_chain = self.llama_prompt | self.llm
        log.info("ragChat initialized successfully.")

    # def vector_augment_prompt(self, query, top_k_value, document_ids):
    #     """
    #     Augments a query prompt with retrieved knowledge based on top-k similarity search.
    #     """
    #     query_list = [query]

    #     try:
    #         # Encoding the query and searching for the most relevant vector
    #         embed_query = self.embed_model.encode(
    #             query_list, show_progress_bar=False
    #         ).tolist()

    #         max_tokens_for_knowledge = (
    #             self.max_context
    #             - len(self.tokenizer.encode(query))
    #             - len(self.tokenizer.encode(self.prompt))
    #             - 100
    #         )

    #         log.info("Performing similarity search for top-k results.")

    #         results = self.index.similarity_search_with_score_by_vector(
    #             embedding=embed_query[0],
    #             space_type="cosineSimilarity",
    #             search_type="painless_scripting",
    #             k=top_k_value,
    #             vector_field="pubmed_bert_vector",
    #             text_field="abstract_chunk",
    #             request_timeout=10,
    #             pre_filter={"terms": {"documentID":document_ids}}
    #         )

    #         source_knowledge, retrieved_ids = self.process_results(
    #             results, max_tokens_for_knowledge
    #         )
    #         log.info(
    #             f"Knowledge augmented successfully. Retrieved {len(retrieved_ids)} IDs."
    #         )
    #         return source_knowledge, retrieved_ids
    #     except Exception as e:
    #         logging.error(f"Failed to augment prompt: {e}")
    #         raise


    def process_results(self, results, max_tokens_for_knowledge):
        """
        Processes results from a similarity search to fit within token limits
        and dynamically determines the top K results to further process based
        on a variety of truncation approaches using a strategy pattern.

        **IMPORTANT**: dynamic_k selection will be implemented in this function

        Args:
            results (list): List of results from a similarity search.
            max_tokens_for_knowledge (int): Maximum number of tokens allowed in the accumulated knowledge.

        Returns:
            tuple: A tuple containing the concatenated knowledge text and a list of retrieved document IDs.
        """
        source_knowledge = ""
        truncate_index = len(results)
        truncated_results = []
        retrieved_ids = []

        truncated_results = results[:truncate_index]

        for result, _ in tqdm(
            truncated_results, desc="Processing search results", leave=False
        ):
            text = result.page_content
            updated_knowledge = (
                source_knowledge + ("\n" if source_knowledge else "") + text
            )
            
            new_tokens_num = len(self.tokenizer.encode(updated_knowledge))
            if new_tokens_num > max_tokens_for_knowledge:
                logging.warning("Token limit reached, stopping knowledge accumulation.")
                break

            source_knowledge = updated_knowledge
            retrieved_ids.append(result.metadata["documentID"])

        unique_ids = list(set(retrieved_ids))
        return source_knowledge, unique_ids[:5]
    

    def vector_augment_prompt_api(self, query, top_k_value, document_ids):
        """
        Augments a query prompt with retrieved knowledge based on top-k similarity search for API requests.
        """
        try:
            query_list = [query]

            # Encoding the query
            embed_query = self.embed_model.encode(
                query_list, show_progress_bar=False
            ).tolist()

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
                                "filter": [
                                    {
                                        "terms": {
                                            "documentID": document_ids
                                        }
                                    }
                                ]
                            }
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_value, doc[\"pubmed_bert_vector\"]) + 1.0",
                            "params": {
                                "query_value": embed_query[0]
                            }
                        }
                    }
                },
                "_source": ["abstract_chunk", "documentID", "abstract_chunk_id"],
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
                        page_content=hit["_source"]["abstract_chunk"],  # Adjust field names
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
            logging.error(f"Failed to augment prompt: {e}")
            raise
