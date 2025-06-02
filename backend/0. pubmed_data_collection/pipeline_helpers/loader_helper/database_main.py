import logging
from typing import List

from opensearchpy import OpenSearch

import utils
from pipeline_helpers.loader_helper.database_mapping import opensearch_complete_mapping
from pipeline_helpers.loader_helper.database_create import opensearch_create

# Initialize logger
log = logging.getLogger(__name__)

# Load configuration from environment
CONFIG = utils.load_config_from_env()


def opensearch_connection(index_names: List[str]) -> OpenSearch:
    """
    Establish a secure connection to an OpenSearch cluster and create the index if not present.

    Args:
        index_names (List[str]): A list containing the name(s) of index(es) to create.

    Returns:
        OpenSearch: An authenticated OpenSearch client instance.

    Raises:
        KeyError: If any required configuration parameter is missing.
        Exception: If index creation or connection setup fails.
    """
    try:
        # Extract credentials and cluster settings from config
        user_name = CONFIG["OPENSEARCH_USERNAME"]
        password = CONFIG["OPENSEARCH_PASSWORD"]
        host = CONFIG["CLUSTER_CHAT_OPENSEARCH_HOST"]
        port = CONFIG["OPENSEARCH_PORT"]

        # Initialize OpenSearch client
        os_client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(user_name, password),
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

        log.info("Successfully established OpenSearch connection")

        # Apply index mapping and create the index if it does not exist
        os_index_mapping = opensearch_complete_mapping()
        opensearch_create(os_client, index_names[0], os_index_mapping)
        log.info("Ensured existence of index: '%s'", index_names[0])

        return os_client

    except Exception as e:
        log.exception(
            "Error occurred while establishing OpenSearch connection: %s", str(e)
        )
        raise
