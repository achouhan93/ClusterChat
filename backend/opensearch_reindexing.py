from opensearchpy import OpenSearch, helpers
import dotenv
from tqdm import tqdm

def load_config_from_env():
    """_summary_

    Returns:
        dict: loads all configration data from dotenv file
    """

    DOTENVPATH = dotenv.find_dotenv()
    CONFIG = dotenv.dotenv_values(DOTENVPATH)

    return CONFIG

CONFIG = load_config_from_env()

# Function to create OpenSearch connection
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

# Reindex function
def reindex_data(source_index, dest_index, batch_size=10000):
    # Define the query to retrieve all documents from the source index
    query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "articleDate": {
                    "order": "desc"
                }
            }
        ]
    }

    # Use a scroll API to fetch data from the source index in batches
    scroll = '2m'  # Keep the search context alive for 2 minutes
    docs = helpers.scan(
        client=client,
        query=query,
        index=source_index,
        scroll=scroll,
        size=batch_size  # Number of documents to fetch per batch
    )

    actions = []
    for doc in tqdm(docs):
        # Prepare each document to be indexed into the destination index
        action = {
            "_op_type": "index",
            "_index": dest_index,
            "_id": doc['_id'],  # Keep the original document ID
            "_source": doc['_source']  # Copy the source content
        }
        actions.append(action)

        # Bulk index the batch into the destination index
        if len(actions) >= batch_size:
            helpers.bulk(client, actions)
            print(f"Indexed {len(actions)} documents")
            actions = []  # Reset actions list after bulk indexing

    # Index any remaining documents
    if actions:
        helpers.bulk(client, actions)
        print(f"Indexed {len(actions)} documents")

    print("Reindexing completed")

# Create the OpenSearch client
client = opensearch_connection()

# Source and destination index names
source_index = 'frameintell_pubmed_sentence_embeddings'  # The current index
dest_index = 'frameintell_pubmed_sentence_embeddings_lucene'  # The new index with Lucene

# Start reindexing
reindex_data(source_index, dest_index)