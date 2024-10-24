import utils
from langchain_community.vectorstores import OpenSearchVectorSearch

CONFIG = utils.loadConfigFromEnv()


class ragLoader:
    def __init__(self) -> None:
        pass

    def get_opensearch_index(self, embedding_model, index):
        user_name = CONFIG["OPENSEARCH_USERNAME"]
        password = CONFIG["OPENSEARCH_PASSWORD"]

        docsearch = OpenSearchVectorSearch(
            embedding_function=embedding_model,
            opensearch_url=f"https://{CONFIG['CLUSTER_TALK_OPENSEARCH_HOST']}",
            index_name=index,
            http_auth=(user_name, password),
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            engine="lucene"
        )

        return docsearch
