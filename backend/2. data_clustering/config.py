"""
Configuration parameters for the clustering pipeline.
"""

BATCH_SIZE = 1000  # Adjust based on available memory
REDUCED_DIM = 50
FINAL_DIM = 2

DIMENSIONALITY_REDUCTION_METHOD = "IncrementalPCA"  # Options: 'UMAP', 'IncrementalPCA'
CLUSTERING_METHOD = "BIRCH"  # Options: 'HDBSCAN', 'BIRCH'

INTERMEDIATE_STORAGE_PATH = "./intermediate_results/"
INDEX_NAME = "frameintell_clustertalk_cluster_information"  # Update with your index name