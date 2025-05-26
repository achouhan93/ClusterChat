from opensearchpy.helpers import bulk
from opensearchpy import NotFoundError
import logging
from tqdm import tqdm

log = logging.getLogger(__name__)
BATCH_SIZE = 50
MAX_PATH_BYTES = 32766


def create_cluster_index(os_connection, cluster_index_name):
    """
    Create the cluster index in OpenSearch if it doesn't exist.
    """
    if not os_connection.indices.exists(index=cluster_index_name):
        cluster_index_body = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "modified_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "preserve_original"],
                        }
                    },
                    "filter": {
                        "preserve_original": {
                            "type": "word_delimiter",
                            "preserve_original": True,
                        }
                    },
                },
                "knn": True,
            },
            "mappings": {
                "properties": {
                    "cluster_id": {"type": "keyword"},
                    "label": {"type": "text", "analyzer": "modified_analyzer"},
                    "topic_information": {"type": "object"},
                    "description": {"type": "text", "analyzer": "modified_analyzer"},
                    "topic_words": {"type": "text"},
                    "x": {"type": "float"},
                    "y": {"type": "float"},
                    "depth": {"type": "integer"},
                    "path": {"type": "keyword"},
                    "is_leaf": {"type": "boolean"},
                    "children": {"type": "keyword"},
                    "cluster_embedding": {
                        "type": "knn_vector",
                        "dimension": 768,
                        "method": {
                            "engine": "lucene",
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "parameters": {"ef_construction": 40, "m": 8},
                        },
                    },  # Cluster embedding vector
                    "pairwise_similarity": {"type": "object"},
                }
            },
        }
        os_connection.indices.create(index=cluster_index_name, body=cluster_index_body)


def index_clusters(os_connection, cluster_index_name, clusters, cluster_embeddings):
    """
    Index clusters into OpenSearch.
    """
    log.info(f"Indexing the cluster information in OpenSearch started")
    cluster_actions = []

    for cluster_id, cluster in tqdm(
        clusters.items(), total=len(clusters), desc="indexing cluster information"
    ):
        # --- Check if the document already exists in OpenSearch ---
        try:
            os_connection.get(index=cluster_index_name, id=cluster_id)
            log.debug(f"Cluster {cluster_id} already exists in OpenSearch. Skipping.")
            continue  # Skip if already exists
        except NotFoundError:
            pass  # Proceed with indexing
        except Exception as e:
            log.error(f"Error checking existence of cluster {cluster_id}: {e}")
            continue  # Skip on unexpected error

        try:
            formatted_topic_information = (
                [
                    {"word": word, "score": score}
                    for word, score in cluster["topic_information"]
                ]
                if cluster["topic_information"] is not None
                else None
            )
            formatted_pairwise_similarity = [
                {"other_cluster_id": other_id, "similarity_score": score}
                for other_id, score in cluster["pairwise_similarity"].items()
            ]

            # --- Safe truncation for path ---
            raw_path = cluster.get("path", "")
            if (
                isinstance(raw_path, str)
                and len(raw_path.encode("utf-8")) > MAX_PATH_BYTES
            ):
                log.warning(
                    f"Truncating 'path' for cluster {cluster_id} to fit byte limit"
                )
                truncated_path = raw_path.encode("utf-8")[: MAX_PATH_BYTES - 10].decode(
                    "utf-8", errors="ignore"
                )
            else:
                truncated_path = raw_path

            action = {
                "_index": cluster_index_name,
                "_id": cluster_id,
                "_source": {
                    "cluster_id": cluster["cluster_id"],
                    "label": cluster["label"],
                    "topic_information": formatted_topic_information,
                    "description": cluster["description"],
                    "topic_words": cluster["topic_words"],
                    "is_leaf": cluster["is_leaf"],
                    "depth": cluster["depth"],
                    "path": truncated_path,
                    "x": cluster["x"],
                    "y": cluster["y"],
                    "children": cluster["children"] if "children" in cluster else [],
                    "cluster_embedding": cluster_embeddings[cluster_id].tolist(),
                    "pairwise_similarity": formatted_pairwise_similarity,
                },
            }
            cluster_actions.append(action)
        except Exception as e:
            log.error(f"Error formatting cluster {cluster_id}: {e}")
            continue

        # Perform bulk indexing in batches
        if len(cluster_actions) == BATCH_SIZE:
            try:
                bulk(os_connection, cluster_actions)
                log.info(f"Indexed {BATCH_SIZE} clusters into OpenSearch.")
            except Exception as e:
                log.error(f"Error indexing batch ending with cluster {cluster_id}: {e}")

            cluster_actions.clear()

    # Index any remaining actions
    if cluster_actions:
        try:
            bulk(os_connection, cluster_actions)
            log.info(
                f"Indexed remaining {len(cluster_actions)} clusters into OpenSearch."
            )
        except Exception as e:
            log.error(f"Error indexing final batch: {e}")

    log.info(f"Indexing the cluster information in OpenSearch completed")
