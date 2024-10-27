import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from opensearchpy.helpers import bulk
import logging
import gc
import logging

log = logging.getLogger(__name__)


def create_document_index(os_connection, document_index_name):
    """
    Create the document index in OpenSearch if it doesn't exist.
    """
    if not os_connection.indices.exists(index=document_index_name):
        document_index_body = {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"},
                    "date": {"type": "date"},
                    "authors:name": {"type": "text"},
                    "authors:affiliation": {"type": "text"},
                    "keywords:name": {"type": "text"},
                    "meshTerms": {"type": "text"},
                    "chemicals": {"type": "text"},
                    "journal:title": {"type": "text"},
                    "cluster_id": {"type": "keyword"},
                    "x": {"type": "float"},
                    "y": {"type": "float"},
                }
            }
        }
        os_connection.indices.create(
            index=document_index_name, body=document_index_body
        )


def index_documents(
    os_connection,
    document_index_name,
    data_fetcher,
    umap_model,
    merged_topic_embeddings_array
):
    """
    Fetches documents, assigns clusters, transforms embeddings, and indexes them into OpenSearch.
    """
    logging.info(f"Started indexing document information")
    # Fetch and process documents in batches
    for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings():
        # Convert embeddings to numpy array
        document_embeddings = np.vstack(embeddings_batch)

        # Compute similarities and assign topics
        similarity = cosine_similarity(
            document_embeddings, merged_topic_embeddings_array
        )
        assigned_topics = np.argmax(similarity, axis=1)
        logging.info(f"UMAP embedding creation for the batch")

        document_umap_embeddings = []
        batch_size = 500  # Adjust batch size as needed
        for i in range(0, len(document_embeddings), batch_size):
            batch = document_embeddings[i : i + batch_size]
            document_umap_embeddings.extend(umap_model.transform(batch))

        # Transform document embeddings using the pre-fitted UMAP model
        document_umap_embeddings = np.array(document_umap_embeddings)
        x_coords = document_umap_embeddings[:, 0]
        y_coords = document_umap_embeddings[:, 1]

        # Prepare documents for indexing
        document_actions = []
        for idx, doc_info in enumerate(ids_batch):
            action = {
                "_index": document_index_name,
                "_id": str(doc_info["documentID"]),
                "_source": {
                    "document_id": doc_info["documentID"],
                    "title": doc_info["title"],
                    "abstract": doc_info.get("abstract_chunk"),
                    "date": doc_info["articleDate"],
                    "authors:name": doc_info["authors:name"],
                    "authors:affiliation": doc_info["authors:affiliation"],
                    "keywords:name": doc_info["keywords:name"],
                    "meshTerms": doc_info["meshTerms"],
                    "chemicals": doc_info["chemicals"],
                    "journal:title": doc_info["journal:title"],
                    "cluster_id": str(assigned_topics[idx]),
                    "x": float(x_coords[idx]),
                    "y": float(y_coords[idx]),
                },
            }

            # Add to actions list
            document_actions.append(action)

            # Index in batches to OpenSearch
            if len(document_actions) >= 1000:
                bulk(os_connection, document_actions)
                logging.info(f"Inserted {len(document_actions)} document information in OpenSearch")
                document_actions = []

        # Index any remaining documents in the current batch
        if document_actions:
            bulk(os_connection, document_actions)

        # Clean up variables to free memory
        del document_embeddings
        gc.collect()

    logging.info(f"Document Indexing Pipeline completed")
