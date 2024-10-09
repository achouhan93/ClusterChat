"""
Module for clustering algorithms.
"""

import numpy as np
from sklearn.cluster import Birch
import hdbscan
from utils import log_time_memory


class ClusteringModel:
    """Class to perform clustering."""

    def __init__(self, method="BIRCH"):
        """
        Initialize the ClusteringModel.

        Args:
            method (str): Clustering method ('HDBSCAN' or 'BIRCH').
        """
        self.method = method
        self.model = None

    @log_time_memory
    def fit(self, data_generator):
        """
        Fits the clustering model on the data.

        Args:
            data_generator (generator): Generator yielding batches of reduced embeddings.
        """
        if self.method == "BIRCH":
            self.model = Birch(
                threshold=0.5,
                branching_factor=50,
                n_clusters=None,
                compute_labels=False,
            )
            for reduced_batch, _ in data_generator():
                self.model.partial_fit(reduced_batch)
            # Optionally set n_clusters and refit to assign labels
            self.model.set_params(n_clusters=None)
            self.model.fit(None)
        elif self.method == "HDBSCAN":
            # Collect data for HDBSCAN fitting
            data = []
            for reduced_batch, _ in data_generator():
                data.append(reduced_batch)
            data = np.vstack(data)
            self.model = hdbscan.HDBSCAN(min_cluster_size=50)
            self.model.fit(data)
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")

    @log_time_memory
    def predict(self, embeddings):
        """
        Predicts cluster labels for the given embeddings.

        Args:
            embeddings (np.ndarray): Reduced embeddings.

        Returns:
            np.ndarray: Cluster labels.
        """
        if self.method == "BIRCH":
            return self.model.predict(embeddings)
        elif self.method == "HDBSCAN":
            # HDBSCAN labels are assigned during fit
            return self.model.labels_
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")

    def get_cluster_info(self):
        """
        Retrieves cluster information.

        Returns:
            dict: Cluster information (e.g., labels, cluster centers).
        """
        if self.method == "BIRCH":
            cluster_info = {
                "n_clusters": len(self.model.subcluster_centers_),
                "subcluster_centers": self.model.subcluster_centers_,
                "labels": self.model.labels_,
            }
            return cluster_info
        elif self.method == "HDBSCAN":
            cluster_info = {
                "labels": self.model.labels_,
                "probabilities": self.model.probabilities_,
                "cluster_persistence": self.model.cluster_persistence_,
            }
            return cluster_info
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")