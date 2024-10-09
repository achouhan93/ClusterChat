"""
Module for handling storage of intermediate and final results.
"""

import os
import numpy as np
import joblib
from opensearchpy import helpers
import config


class StorageManager:
    """Class to handle storage operations."""

    def __init__(self, opensearch_connection):
        """
        Initialize the StorageManager.

        Args:
            opensearch_connection (OpenSearch): OpenSearch client connection.
        """
        self.intermediate_path = config.INTERMEDIATE_STORAGE_PATH
        os.makedirs(self.intermediate_path, exist_ok=True)
        self.client = opensearch_connection

    def save_intermediate(self, filename, data):
        """
        Saves intermediate data to disk.

        Args:
            filename (str): Name of the file.
            data: Data to save.
        """
        filepath = os.path.join(self.intermediate_path, filename)
        joblib.dump(data, filepath)

    def load_intermediate(self, filename):
        """
        Loads intermediate data from disk.

        Args:
            filename (str): Name of the file.

        Returns:
            Data loaded from the file.
        """
        filepath = os.path.join(self.intermediate_path, filename)
        return joblib.load(filepath)

    def store_results(self, embeddings_2d, ids, labels):
        """
        Stores the final results in OpenSearch.

        Args:
            embeddings_2d (np.ndarray): 2D embeddings.
            ids (list): List of document metadata dictionaries.
            labels (np.ndarray): Cluster labels.
        """
        actions = []
        for idx, doc_meta in enumerate(ids):
            action = {
                "_op_type": "update",
                "_index": config.INDEX_NAME,
                "_id": doc_meta["documentID"],
                "doc": {
                    "x": float(embeddings_2d[idx, 0]),
                    "y": float(embeddings_2d[idx, 1]),
                    "cluster_label": int(labels[idx]),
                },
            }
            actions.append(action)

            if len(actions) == config.BATCH_SIZE:
                helpers.bulk(self.client, actions)
                actions = []

        if actions:
            helpers.bulk(self.client, actions)

    def store_cluster_info(self, cluster_info):
        """
        Stores cluster information in OpenSearch.

        Args:
            cluster_info (dict): Information about the clusters (e.g., cluster centers).
        """
        index_name = config.CLUSTER_INFO_INDEX  # Define this in your config.py
        actions = []

        subcluster_centers = cluster_info.get("subcluster_centers")
        n_clusters = cluster_info.get("n_clusters")

        for idx, center in enumerate(subcluster_centers):
            action = {
                "_op_type": "index",
                "_index": index_name,
                "_id": f"cluster_{idx}",
                "_source": {
                    "cluster_id": idx,
                    "center": center.tolist(),
                    "n_clusters": n_clusters,
                },
            }
            actions.append(action)

            if len(actions) == config.BATCH_SIZE:
                helpers.bulk(self.client, actions)
                actions = []

        if actions:
            helpers.bulk(self.client, actions)