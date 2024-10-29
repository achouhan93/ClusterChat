"""
Configuration parameters for the clustering pipeline.
"""

BATCH_SIZE = 5000  # Adjust based on available memory
REDUCED_DIM = 50
FINAL_DIM = 2

DIMENSIONALITY_REDUCTION_METHOD = "IncrementalPCA"  # Options: 'UMAP', 'IncrementalPCA'
CLUSTERING_METHOD = "BIRCH"  # Options: 'HDBSCAN', 'BIRCH'

MODEL_PATH = "./intermediate_results/"

# Index names
CLUSTER_INFO_INDEX_NAME = (
    "frameintell_clustertalk_cluster_information"  # For cluster info
)
RESULTS_INDEX_NAME = "frameintell_clustertalk_results"  # For per-document results

# Index mappings
CLUSTER_INFO_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "cluster_id": {"type": "integer"},
            "center": {"type": "dense_vector", "dims": REDUCED_DIM},
            "n_clusters": {"type": "integer"},
        }
    }
}

RESULTS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "documentID": {"type": "keyword"},
            "x": {"type": "float"},
            "y": {"type": "float"},
            "cluster_label": {"type": "integer"},
        }
    }
}
