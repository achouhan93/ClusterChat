import re
import logging
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch, RequestsHttpConnection


def setup_logging():
    """Setup logging configuration."""

    logging.basicConfig(
        filename="embedding_generation.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def connect_opensearch(host, port, username, password):
    """Connect to OpenSearch.

    Args:
        host: OpenSearch host
        port: OpenSearch port
        username: Account Username
        password: Account Password

    Returns:
        Returns OpenSearch client object.
    """

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(username, password),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=60,
    )
    return client


def get_end_date(client):
    """Get the update_date of the oldest arXiv Paper from the source index.
    This date will then be used as the end_date
    till which the embeddings will be generated.

    Args:
        client: OpenSearch client object

    Returns:
        The update_date of the oldest arXiv Paper.
    """

    query = {
        "size": 1,
        "_source": ["update_date"],
        "query": {"match_all": {}},
        "sort": [{"update_date": {"order": "asc"}}],
    }
    response = client.search(index="frameintell_arxiv_metadata", body=query)
    end_date = response["hits"]["hits"][0]["_source"]["update_date"]
    return end_date


def get_first_batch(client, start_date, end_date, pit_id, batch_size=1000):
    """Get the first batch of arXiv Papers from the source index.
    Uses a default batch size of 1000 if not provided.
    Point in Time API ID is kept alive for 60 minutes
    to keep the search context alive in case of large batch sizes.

    Args:
        client: OpenSearch client object
        start_date: The date from which the embeddings will be generated.
        end_date: The date till which the embeddings will be generated.
        pit_id: Point in Time ID to keep the search context alive.
        batch_size: Number of documents to be processed at once. Defaults to 1000.

    Returns:
        The first batch of arXiv Papers and the query used to fetch them.
    """

    query = {
        "size": batch_size,
        "_source": ["id", "abstract", "update_date"],
        "query": {"range": {"update_date": {"lte": start_date, "gte": end_date}}},
        "sort": [{"update_date": {"order": "desc"}}, {"_id": "desc"}],
        "pit": {"id": pit_id, "keep_alive": "60m"},
    }
    response = client.search(body=query)
    results = response["hits"]["hits"]
    return results, query


def create_target_index(client, target_index, dimension):
    """Create the target index if it does not exist.

    Args:
        client: OpenSearch client object
        target_index: The name of the target index
        dimension: The dimension of the embedding vector according to the model used.
    """

    mappings = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "abstract": {"type": "text"},
                "processed_abstract": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dimension,
                },
                "update_date": {"type": "date"},
            }
        }
    }
    if not client.indices.exists(index=target_index):
        client.indices.create(index=target_index, body=mappings)
        logging.info(f"Index {target_index} created.")


def process_abstracts(abstracts, stop_words):
    """Process the abstracts by removing newline characters, converting to lowercase,
    removing special characters, whitespaces and removing stopwords.

    Args:
        abstracts: List of abstracts to be processed
        stop_words: Set of stopwords to be used for removal

    Returns:
        List of processed abstracts
    """

    processed_abstracts = []
    for abstract in abstracts:
        if not isinstance(abstract, str):
            processed_abstracts.append("")
            continue
        abstract = abstract.replace("\n", " ")
        abstract = abstract.lower()
        abstract = re.sub(r"[^a-zA-Z\s]", "", abstract)
        words = abstract.split()
        processed_abstract = [word for word in words if word not in stop_words]
        processed_abstract = " ".join(processed_abstract)
        processed_abstracts.append(processed_abstract)
    return processed_abstracts


def disconnect_opensearch(client, pit_id):
    """Disconnect from OpenSearch and delete the Point in Time.

    Args:
        client: OpenSearch client object
        pit_id: Point in Time ID to be deleted after processing.
    """

    client.delete_point_in_time(body={"pit_id": pit_id})
    client.transport.close()


def main():
    # Configuration parameters
    host = "opensearch-ds.ifi.uni-heidelberg.de"
    port = 443
    username = "asiddhpura"
    password = "Pkw?#Rivale9Meran.Abweg"
    source_index = "frameintell_arxiv_metadata"
    target_index = "frameintell_arxiv_embeddings"
    model_name = "Alibaba-NLP/gte-large-en-v1.5"
    batch_size = 1000
    dimension = 1024
    setup_logging()

    # Connect to OpenSearch and create a Point in Time context
    client = connect_opensearch(host, port, username, password)
    pit = client.create_point_in_time(index=source_index, keep_alive="60m")
    pit_id = pit["pit_id"]
    logging.info("Connected to OpenSearch.")
    logging.info(f"Point in Time ID: {pit_id}")

    # Get the first batch of arXiv Papers and create the target index
    start_date = "now"
    end_date = get_end_date(client)
    results, query = get_first_batch(client, start_date, end_date, pit_id, batch_size)
    create_target_index(client, target_index, dimension)
    logging.info(f"Target index {target_index} created.")

    # Load the stopwords and the Sentence Transformer model
    nltk.download("stopwords")
    stop_words = set(stopwords.words("english"))
    model = SentenceTransformer(model_name, trust_remote_code=True)
    logging.info(f"Model {model_name} loaded.")

    # Process the abstracts and generate embeddings
    total_documents_processed = 0
    while True:
        try:
            if not results:
                break

            # Generate embeddings for the abstracts
            abstracts = [result["_source"]["abstract"] for result in results]
            processed_abstracts = process_abstracts(abstracts, stop_words)
            embeddings = model.encode(processed_abstracts, show_progress_bar=False).tolist()

            # Bulk insert the documents into the target index
            bulk_data = []
            for i, result in enumerate(results):
                doc = {
                    "id": result["_source"]["id"],
                    "abstract": result["_source"]["abstract"],
                    "processed_abstract": processed_abstracts[i],
                    "embedding": embeddings[i],
                    "update_date": result["_source"]["update_date"],
                }
                bulk_data.append({"index": {"_index": target_index, "_id": doc["id"]}})
                bulk_data.append(doc)
            client.bulk(body=bulk_data)

            # Log the progress and the last update_date processed
            total_documents_processed += len(results)
            last_update_date = results[-1]["_source"]["update_date"]
            logging.info(f"Total documents processed: {total_documents_processed}")
            logging.info(f"Last update_date: {last_update_date}")

            # Fetch the next batch of arXiv Papers
            last_sort = results[-1]["sort"]
            query["search_after"] = last_sort
            response = client.search(body=query)
            results = response["hits"]["hits"]

        except Exception as e:
            logging.error(f"Error: {e}")
            break

    # Disconnect from OpenSearch and log the completion of the process
    disconnect_opensearch(client, pit_id)
    logging.info("Disconnected from OpenSearch.")
    logging.info("Process completed.")


if __name__ == "__main__":
    main()
