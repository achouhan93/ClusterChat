from opensearchpy.helpers import bulk
import logging

log = logging.getLogger(__name__)


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
                    "topic_information": {
                        "type": "nested",
                        "properties": {
                            "word": {"type": "text"},
                            "score": {"type": "float"},
                        },
                    },
                    "description": {"type": "text", "analyzer": "modified_analyzer"},
                    "topic_words": {"type": "text"},
                    "x": {"type": "float"},
                    "y": {"type": "float"},
                    "depth": {"type": "integer"},
                    "path": {"type": "keyword"},
                    "is_leaf": {"type": "boolean"},
                    "children": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 768,
                        "method": {
                            "engine": "lucene",
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "parameters": {"ef_construction": 40, "m": 8},
                        },
                    },  # Cluster embedding vector
                    "pairwise_similarity": {
                        "type": "nested",
                        "properties": {
                            "other_cluster_id": {"type": "keyword"},
                            "similarity_score": {"type": "float"},
                        },
                    },
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
    for cluster_id, cluster in clusters.items():
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
                "path": cluster["path"],
                "x": cluster["x"],
                "y": cluster["y"],
                "children": cluster["children"] if "children" in cluster else [],
                "embedding": cluster_embeddings[cluster_id].tolist(),
                "pairwise_similarity": formatted_pairwise_similarity,
            },
        }
        cluster_actions.append(action)

    bulk(os_connection, cluster_actions)
    log.info(f"Indexing the cluster information in OpenSearch completed")
