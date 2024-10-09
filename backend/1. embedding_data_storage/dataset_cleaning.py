from opensearchpy import helpers
from utils import loadConfigFromEnv
from tasks import *


CONFIG = loadConfigFromEnv()
os_connection = opensearch_connection()

source_os_index = CONFIG["CLUSTER_TALK_OPENSEARCH_SOURCE_INDEX"]
target_os_index = CONFIG["CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_COMPLETE"]

query = {
    "_source": False,
    "query": {
        "bool": {
            "must": [
                {
                    "match_phrase": {
                        "abstract": "ABSTRACT TRUNCATED"
                    }
                }
            ]
        }
    }
}

# Initialize the scroll
scroll = helpers.scan(
    os_connection,
    query=query,
    index=source_os_index,
    scroll='10m',
    size=10000
)

# Collect IDs
ids_to_delete = []

for doc in scroll:
    if doc['_id'] != "29675559":
        ids_to_delete.append(doc['_id'])

print(f"Total IDs fetched: {len(ids_to_delete)}")

batch_size = 10000  # Adjust as needed

def chunked_iterable(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

for batch_num, batch_ids in enumerate(chunked_iterable(ids_to_delete, batch_size), start=1):
    query = {
        "query": {
            "terms": {
                "documentID": batch_ids
            }
        }
    }
    response = os_connection.delete_by_query(
        index=target_os_index,
        body=query,
        conflicts='proceed',
        refresh=False,
        wait_for_completion=True,
        slices='auto'
    )
    deleted = response.get('deleted', 0)
    print(f"Batch {batch_num}: Deleted {deleted} documents.")

# Refresh the index after deletions are complete
os_connection.indices.refresh(index=target_os_index)
