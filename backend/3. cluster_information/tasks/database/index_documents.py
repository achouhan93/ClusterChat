import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from opensearchpy.helpers import bulk
import logging
import gc
import psutil
from time import sleep
import os

log = logging.getLogger(__name__)


def _log_memory_usage():
    if psutil:
        mem = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
        log.info(f"[Memory Usage] Current process memory: {mem:.2f} GB")


def create_document_index(os_connection, document_index_name):
    """
    Create the document index in OpenSearch if it doesn't exist.
    """
    if not os_connection.indices.exists(index=document_index_name):
        document_index_body = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "knn": True,
            },
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
                    "pubmed_bert_vector": {
                        "type": "knn_vector",
                        "dimension": 768,
                        "method": {
                            "engine": "lucene",
                            "space_type": "cosinesimil",
                            "name": "hnsw",
                            "parameters": {"ef_construction": 40, "m": 8},
                        },
                    },
                }
            },
        }
        os_connection.indices.create(
            index=document_index_name, body=document_index_body
        )


def index_documents(
    os_connection,
    document_index_name,
    data_fetcher,
    umap_model,
    merged_topic_embeddings_array,
    batch_size_umap=500,
    batch_size_indexing=1000,
):
    """
    Fetches documents, assigns clusters, transforms embeddings, and indexes them into OpenSearch.
    """
    log.info(f"Started indexing document information")

    try:
        # Fetch and process documents in batches
        for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings():
            # Convert embeddings to numpy array
            document_embeddings = np.vstack(embeddings_batch)

            # --- Topic Assignment ---
            # Compute similarities and assign topics
            similarity = cosine_similarity(
                document_embeddings, merged_topic_embeddings_array
            )
            assigned_topics = np.argmax(similarity, axis=1)

            # --- UMAP Transformation ---
            log.info(f"UMAP embedding creation for the batch")

            document_umap_embeddings = []

            for i in range(0, len(document_embeddings), batch_size_umap):
                batch = document_embeddings[i : i + batch_size_umap]

                try:
                    transformed = umap_model.transform(batch)
                    document_umap_embeddings.extend(transformed)
                except Exception as e:
                    log.error(f"UMAP transformation failed on batch {i}: {str(e)}")
                    document_umap_embeddings.extend([[0.0, 0.0]] * len(batch))

            # Transform document embeddings using the pre-fitted UMAP model
            document_umap_embeddings = np.array(document_umap_embeddings)
            x_coords = document_umap_embeddings[:, 0]
            y_coords = document_umap_embeddings[:, 1]

            # --- Document Preparation ---
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
                        "pubmed_bert_vector": document_embeddings[idx].tolist(),
                    },
                }

                # Add to actions list
                document_actions.append(action)

                # Index in batches to OpenSearch
                if len(document_actions) >= batch_size_indexing:
                    bulk(os_connection, document_actions)
                    log.info(
                        f"Inserted {len(document_actions)} document information in OpenSearch"
                    )
                    document_actions = []

            # Index any remaining documents in the current batch
            if document_actions:
                bulk(os_connection, document_actions)
                log.info(
                    f"Inserted final {len(document_actions)} documents of current batch."
                )

            _log_memory_usage()

            # Clean up variables to free memory
            del document_embeddings
            del document_umap_embeddings
            del transformed
            del document_actions
            del similarity
            del assigned_topics

            gc.collect()
            sleep(2)
            _log_memory_usage()

    except Exception as e:
        log.error(f"Batch processing failed: {str(e)}")

    log.info(f"Document Indexing Pipeline completed")
