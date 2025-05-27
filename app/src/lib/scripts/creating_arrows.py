from opensearchpy import OpenSearch
import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
import dotenv


def loadConfigFromEnv():
    DOTENVPATH = dotenv.find_dotenv()
    CONFIG = dotenv.dotenv_values(DOTENVPATH)

    return CONFIG


def opensearch_connection(CONFIG):

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

# query opensearch for the 100K records, 10K at a time 
def fetch_opensearch_records(client, index_name,scroll_time, query):

    response = client.search(
        index=index_name,
        scroll=	scroll_time,
        size=10000,
        body=query
    )

    scroll_id = response['_scroll_id']
    all_hits = response['hits']['hits']

    #### Test for the first 10K Records

    while True:
        scroll_response = client.scroll(scroll_id=scroll_id, scroll=scroll_time)
        hits = scroll_response['hits']['hits']
        if not hits:
            break
        all_hits.extend(hits)
        scroll_id = scroll_response['_scroll_id'] 


    return [doc['_source'] for doc in all_hits]

# convert the docs into pandas and then into parquet


if __name__ == "__main__":

    CONFIG = loadConfigFromEnv()
    os_client = opensearch_connection(CONFIG)
    index_name = CONFIG["CLUSTER_TALK_DOCUMENT_INFORMATION_INDEX"]
    scroll_time = "2m"
    query =  {
				"query": {
					"match_all": {}
				},
				"_source": {
					"includes": ['document_id', 'x', 'y', 'title', 'date', 'cluster_id']
				}
			}

    records = fetch_opensearch_records(os_client,index_name,scroll_time,query)
    table = pa.Table.from_pylist(records)

    with pa.OSFile("output.arrow", 'wb') as sink:
        with ipc.new_file(sink, table.schema) as writer:
            writer.write(table)
		
    
    
