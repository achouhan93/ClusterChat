import logging
from typing import Any

from opensearchpy import OpenSearch

import utils

# Configure logger
logger = logging.getLogger(__name__)

# Load environment-based configuration
CONFIG = utils.load_config_from_env()


def opensearch_connection() -> OpenSearch:
    """
    Establishes a secure connection to an OpenSearch cluster.

    Returns:
        OpenSearch: An authenticated OpenSearch client instance.

    Raises:
        KeyError: If required configuration keys are missing.
        Exception: If connection initialization fails for any other reason.
    """
    try:
        # Retrieve credentials and host details from environment configuration
        username: str = CONFIG["OPENSEARCH_USERNAME"]
        password: str = CONFIG["OPENSEARCH_PASSWORD"]
        host: str = CONFIG["CLUSTER_CHAT_OPENSEARCH_HOST"]
        port: int = int(CONFIG["OPENSEARCH_PORT"])

        # Initialize OpenSearch client
        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(username, password),
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

        logger.info("OpenSearch connection established..")
        return client

    except KeyError as ke:
        logger.error(f"Missing configuration key: {str(ke)}")
        raise

    except Exception as e:
        logger.exception(f"Failed to initialize OpenSearch connection: {str(e)}")
        raise
