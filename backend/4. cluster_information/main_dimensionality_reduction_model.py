from opensearchpy import OpenSearch
from sklearn.utils import shuffle
import umap
import numpy as np
import joblib
import os
import dotenv
from tqdm import tqdm

def loadConfigFromEnv():
    """_summary_

    Returns:
        dict: loads all configration data from dotenv file
    """

    DOTENVPATH = dotenv.find_dotenv()
    CONFIG = dotenv.dotenv_values(DOTENVPATH)

    return CONFIG

CONFIG = loadConfigFromEnv()

# Connect to OpenSearch (Update this with your specific connection details)
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
        hosts=[{"host": CONFIG["CLUSTER_TALK_OPENSEARCH_HOST"], "port": CONFIG["OPENSEARCH_PORT"]}],
        http_auth=(user_name, password),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )

    return os

def fetch_sample_embeddings(client, index_name, sample_size=1000000, batch_size=10000):
    """
    Fetch a sample of embeddings from OpenSearch.

    Args:
        client (OpenSearch): OpenSearch client connection.
        index_name (str): Name of the index to fetch data from.
        sample_size (int): Number of records to sample.
        batch_size (int): Number of records to fetch per batch.

    Returns:
        np.ndarray: Array of embeddings sampled from OpenSearch.
    """
    start_date = "2020-01-01"
    end_date = "2024-07-31"
    search_params = {
        "_source": ["pubmed_bert_vector"],
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "articleDate": {
                                "gte": start_date,
                                "lte": end_date
                            }
                        }
                    }
                ]
            }
        }
    }
    
    embeddings = []
    scroll_id = None

    # Fetch batches from OpenSearch
    response = client.search(
        index=index_name, 
        body=search_params, 
        scroll="5m", 
        size=batch_size
        )
    scroll_id = response["_scroll_id"]
    hits = response["hits"]["hits"]

    with tqdm(total=sample_size) as pbar:
        while hits and len(embeddings) < sample_size:
            for doc in tqdm(hits):
                embedding = doc["_source"].get("pubmed_bert_vector")
                if embedding:
                    embeddings.append(embedding)

            pbar.update(len(hits))        
            response = client.scroll(scroll_id=scroll_id, scroll="5m")
            hits = response["hits"]["hits"]
            scroll_id = response["_scroll_id"]

        # Stop scrolling and cleanup
        client.clear_scroll(scroll_id=scroll_id)
    
    # Shuffle and limit to sample size
    embeddings = np.array(embeddings, dtype=np.float32)
    embeddings = shuffle(embeddings, random_state=42)
    
    return embeddings

def fit_umap_models(embeddings, output_dir):
    """
    Fit UMAP models with 50 and 2 components and save them.

    Args:
        embeddings (np.ndarray): Array of sampled embeddings.
        output_dir (str): Directory to save the UMAP models.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # UMAP model for 50 components
    print("Training UMAP model with 50 components...")
    umap_50 = umap.UMAP(n_components=50, n_jobs=1, random_state=42)
    embeddings_50 = umap_50.fit_transform(embeddings)
    joblib.dump(umap_50, os.path.join(output_dir, "umap_50_components.joblib"))
    print("UMAP model with 50 components saved.")

    # UMAP model for 2 components
    print("Training UMAP model with 2 components...")
    umap_2 = umap.UMAP(n_components=2, n_jobs=1, random_state=42)
    embeddings_2 = umap_2.fit_transform(embeddings_50)  # Transform 50D reduced embeddings to 2D
    joblib.dump(umap_2, os.path.join(output_dir, "umap_2_components.joblib"))
    print("UMAP model with 2 components saved.")

# Main script
if __name__ == "__main__":
    # Configuration
    INDEX_NAME = "frameintell_pubmed_abstract_embeddings"
    SAMPLE_SIZE = 400000  # Adjust based on available memory and sample representativeness
    OUTPUT_DIR = "umap_models"
    
    # Step 1: Fetch sample data
    client = opensearch_connection()
    embeddings = fetch_sample_embeddings(client, INDEX_NAME, SAMPLE_SIZE)
    print(f"Fetched {embeddings.shape[0]} records for training UMAP.")

    # Step 2: Fit UMAP models
    fit_umap_models(embeddings, OUTPUT_DIR)
