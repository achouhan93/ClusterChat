import json
import fileinput
from tqdm import tqdm
from opensearchpy import OpenSearch, RequestsHttpConnection

# Connect to the OpenSearch instance
os = OpenSearch(
    hosts=[{"host": "opensearch-ds.ifi.uni-heidelberg.de", "port": 443}],
    http_auth=("asiddhpura", "Pkw?#Rivale9Meran.Abweg"),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=120,
)
# Old index mapping
# mappings_old = {
#     "mappings": {
#         "properties": {
#             "id": {"type": "keyword"},
#             "submitter": {"type": "text"},
#             "authors": {"type": "text"},
#             "title": {"type": "text", "analyzer": "standard"},
#             "comments": {"type": "text"},
#             "journal-ref": {"type": "text"},
#             "doi": {"type": "keyword"},
#             "categories": {"type": "keyword"},
#             "abstract": {"type": "text", "analyzer": "english"},
#             "versions": {
#                 "type": "nested",
#                 "properties": {
#                     "version": {"type": "keyword"},
#                     "created": {"type": "date", "format": "EEE, d MMM yyyy HH:mm:ss 'GMT'"},
#                 },
#             },
#             "update_date": {"type": "date", "format": "yyyy-MM-dd"},
#         }
#     }
# }

# Index mapping
mappings = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "submitter": {"type": "text"},
            "authors": {"type": "text"},
            "title": {"type": "text"},
            "comments": {"type": "text"},
            "journal-ref": {"type": "text"},
            "doi": {"type": "keyword"},
            "report-no": {"type": "keyword", "null_value": "null"},
            "categories": {"type": "text"},
            "license": {"type": "keyword", "null_value": "null"},
            "abstract": {"type": "text", "analyzer": "english"},
            "versions": {
                "type": "nested",
                "properties": {
                    "version": {"type": "keyword"},
                    "created": {"type": "date", "format": "EEE, d MMM yyyy HH:mm:ss 'GMT'"},
                },
            },
            "update_date": {"type": "date", "format": "yyyy-MM-dd"},
        }
    }
}


# Create the index
index = "frameintell_arxiv_metadata"
if not os.indices.exists(index=index):
    os.indices.create(index=index, body=mappings)
    print(f"Index {index} created.")


# def index_data_one_by_one(file_path, index_name):
#     with fileinput.input(files=(file_path)) as f:
#         for line in tqdm(f, desc="Indexing data"):
#             document = json.loads(line.strip())
#             try:
#                 response = os.index(index=index_name, id=document["id"], body=document)
#             except Exception as e:
#                 print(f"Error: {e}")
#                 print(f"Document: {document}")
#                 break


# index = "frameintell_arxiv_metadata"
# file_path = "../data/arxiv-metadata-oai-snapshot.json"
# index_data_one_by_one(file_path, index)


# Bulk index the data
def bulk_index_data(file_path, index_name):
    with fileinput.input(files=(file_path)) as f:
        bulk_data = []
        for line in tqdm(f, desc="Bulk indexing data"):
            document = json.loads(line.strip())
            bulk_data.append({"create": {"_index": index_name, "_id": document["id"]}})
            bulk_data.append(document)
            if len(bulk_data) >= 100000:
                os.bulk(bulk_data)
                bulk_data = []
        if bulk_data:
            os.bulk(bulk_data)


index = "frameintell_arxiv_metadata"
file_path = "data/arxiv-metadata-oai-snapshot.json"
bulk_index_data(file_path, index)

# Check the number of documents in the index
response = os.count(index=index)
print(response)
# Search for documents
response = os.search(index=index, body={"query": {"match": {"title": "intelligence"}}, "size": 1})
print(response)
