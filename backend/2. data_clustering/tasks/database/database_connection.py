"""
Module for establishing OpenSearch connection.
"""

import utils
from opensearchpy import OpenSearch

# OpenSearch configuration details
CONFIG = utils.load_config_from_env()


def opensearch_connection():
    """
    Establish the OpenSearch connection.

    Returns:
        OpenSearch: OpenSearch client connection object.
    """
    # OpenSearch Connection Settings
    user_name = CONFIG["OPENSEARCH_USERNAME"]
    password = CONFIG["OPENSEARCH_PASSWORD"]
    os_client = OpenSearch(
        hosts=[
            {
                "host": CONFIG["CLUSTER_TALK_OPENSEARCH_HOST"],
                "port": int(CONFIG["OPENSEARCH_PORT"]),
            }
        ],
        http_auth=(user_name, password),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )

    return os_client
