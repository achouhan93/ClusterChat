import logging
from typing import Any

import utils
from langchain_community.vectorstores import OpenSearchVectorSearch

# Load configuration
CONFIG = utils.load_config_from_env()

# Configure logging
logger = logging.getLogger(__name__)


class RagLoader:
    """
    A class for loading vector search indices from OpenSearch
    for use in Retrieval-Augmented Generation (RAG) pipelines.
    """

    def __init__(self) -> None:
        """Initializes the RagLoader instance."""
        pass

    def get_opensearch_index(
        self, embedding_model: Any, index: str
    ) -> OpenSearchVectorSearch:
        user_name: str = CONFIG["OPENSEARCH_USERNAME"]
        password: str = CONFIG["OPENSEARCH_PASSWORD"]
        host: str = CONFIG["CLUSTER_TALK_OPENSEARCH_HOST"]

        logger.info(
            f"Initializing OpenSearchVectorSearch connection for index: {index}"
        )

        docsearch = OpenSearchVectorSearch(
            embedding_function=embedding_model,
            opensearch_url=f"https://{host}",
            index_name=index,
            http_auth=(user_name, password),
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            engine="lucene",
        )

        logger.info(f"Successfully connected to OpenSearch index: {index}")
        return docsearch
