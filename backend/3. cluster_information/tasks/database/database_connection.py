import utils
from opensearchpy import OpenSearch


# Postgres and OpenSearch configuration details
CONFIG = utils.load_config_from_env()


def opensearch_connection():
    """
    Establish the OpenSearch connection

    Returns:
        object: opensearch connection object
    """
    # OpenSearch Connection Setting
    user_name = CONFIG["OPENSEARCH_USERNAME"]
    password = CONFIG["OPENSEARCH_PASSWORD"]
    os = OpenSearch(
        hosts=[
            {
                "host": CONFIG["CLUSTER_TALK_OPENSEARCH_HOST"],
                "port": CONFIG["OPENSEARCH_PORT"],
            }
        ],
        http_auth=(user_name, password),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )

    return os
