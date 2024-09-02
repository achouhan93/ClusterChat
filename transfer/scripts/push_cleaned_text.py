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

# Index mapping
mappings = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "english"},
            "abstract": {"type": "text", "analyzer": "english"},
            "journal-ref": {"type": "text"},
            "categories": {"type": "text"},
        }
    }
}


# Create the index
index = "frameintell_arxiv_cleaned_text"
if not os.indices.exists(index=index):
    os.indices.create(index=index, body=mappings)
    print(f"Index {index} created.")


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


index = "frameintell_arxiv_cleaned_text"
file_path = "data/cleaned_texts_for_embedding.json"
bulk_index_data(file_path, index)

# Check the number of documents in the index
response = os.count(index=index)
print(response)
# Search for documents
response = os.search(index=index, body={"query": {"match": {"title": "intelligence"}}, "size": 1})
print(response)
