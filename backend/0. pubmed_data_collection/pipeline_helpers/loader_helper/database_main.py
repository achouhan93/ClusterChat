import utils
from opensearchpy import OpenSearch
from pipeline_helpers.loader_helper.database_mapping import opensearch_complete_mapping
from pipeline_helpers.loader_helper.database_create import opensearch_create

CONFIG = utils.load_config_from_env()


def opensearch_connection(index_name):
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

    os_index_mapping = opensearch_complete_mapping()
    opensearch_create(os, index_name[0], os_index_mapping)

    return os
