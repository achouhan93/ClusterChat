import logging
from datetime import datetime
from torch import cuda
from sentence_transformers import SentenceTransformer
import utils
import json
from tqdm import tqdm

from tasks.rag_components import rag_chatmodel, rag_loader, rag_prompt

log = logging.getLogger(__name__)
CONFIG = utils.loadConfigFromEnv()

class Processor:
    """
    Processor class to handle the text processing pipeline including text retrieval
    and generation using language models.
    """
    def __init__(
        self,
        opensearch_connection,
        embedding_os_index,
        embedding_model,
        model_config
    ):
        self.os_connection = opensearch_connection
        self.embeddings_os_index_name = embedding_os_index

        self.device = f"cuda:{cuda.current_device()}" if cuda.is_available() else "cpu"

        self.embed_model = SentenceTransformer(
            model_name_or_path=embedding_model,
            trust_remote_code=True,
            device=self.device,
        )

        self.scroll_size = 100

        self.vector_store = rag_loader.ragLoader().get_opensearch_index(
            self.embed_model, self.embeddings_os_index_name
        )

        self.model_config = model_config

        self.prompt = rag_prompt.ragPrompt().prompt_template()
        self.chat_model = rag_chatmodel.ragChat(
            self.vector_store,
            self.prompt,
            ["context", "question"],
            self.embed_model,
            self.model_config
        )


    def process_api_request(self, question, question_type, document_ids):
        """
        Process an API request to generate an answer based on the question, question type, and document IDs.

        :param question: The user's question as a string.
        :param question_type: Type of question, 'corpus-based' or 'document-specific'.
        :param document_ids: List of document IDs to restrict the search to. If empty, use the whole corpus.
        :return: A tuple (answer, sources)
        """
        try:
            if question_type == 'corpus-based':
                # Use the entire corpus
                context, retrieved_ids = self.chat_model.vector_augment_prompt_api(
                    query=question,
                    top_k_value=10,
                    document_ids=document_ids 
                )
            elif question_type == 'document-specific':
                context, retrieved_ids = self.chat_model.vector_augment_prompt_api(
                    query=question,
                    top_k_value=10,
                    document_ids=document_ids
                )
                # context, retrieved_ids = self.chat_model.vector_augment_prompt(
                #     query=question,
                #     top_k_value=10,
                #     document_ids=document_ids
                # )
            else:
                raise ValueError("Invalid question_type")

            # Generate the answer
            answer = self.chat_model.llm_chain.invoke({"context": context, "question": question})
            cleaned_answer = answer.strip()
            return cleaned_answer, retrieved_ids

        except Exception as e:
            log.error(f"Error processing API request: {e}")
            raise RuntimeError(f"Error processing API request: {e}")