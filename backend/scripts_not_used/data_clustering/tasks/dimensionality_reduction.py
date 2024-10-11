"""
Module for dimensionality reduction.
"""

import numpy as np
from sklearn.decomposition import IncrementalPCA
import umap
import config
from utils import log_time_memory


class DimensionalityReducer:
    """Class to perform dimensionality reduction."""

    def __init__(self, method="IncrementalPCA", n_components=None):
        """
        Initialize the DimensionalityReducer.

        Args:
            method (str): Dimensionality reduction method ('UMAP' or 'IncrementalPCA').
            n_components (int): Number of components for reduction.
        """
        self.method = method
        self.n_components = n_components or config.REDUCED_DIM
        self.reducer = None

    @log_time_memory
    def fit(self, data_generator):
        """
        Fits the dimensionality reduction model on the data.

        Args:
            data_generator (generator): Generator yielding batches of embeddings.
        """
        if self.method == "IncrementalPCA":
            self.reducer = IncrementalPCA(n_components=self.n_components)
            for embeddings_batch, _ in data_generator():
                self.reducer.partial_fit(embeddings_batch)
        elif self.method == "UMAP":
            data = []
            for embeddings_batch, _ in data_generator():
                data.append(embeddings_batch)
            data = np.vstack(data)
            self.reducer = umap.UMAP(n_components=self.n_components, random_state=42)
            self.reducer.fit(data)
        else:
            raise ValueError(f"Unknown dimensionality reduction method: {self.method}")

    @log_time_memory
    def fit_partial(self, embeddings):
        """
        Partially fits the dimensionality reduction model on the embeddings.

        Args:
            embeddings (np.ndarray): Embeddings to fit.
        """
        if self.method == "IncrementalPCA":
            if self.reducer is None:
                self.reducer = IncrementalPCA(n_components=self.n_components)
            self.reducer.partial_fit(embeddings)
        else:
            raise NotImplementedError(
                "fit_partial is only implemented for IncrementalPCA."
            )

    @log_time_memory
    def transform(self, embeddings):
        """
        Transforms embeddings using the fitted model.

        Args:
            embeddings (np.ndarray): Embeddings to transform.

        Returns:
            np.ndarray: Reduced embeddings.
        """
        return self.reducer.transform(embeddings)

    @log_time_memory
    def fit_transform(self, embeddings):
        """
        Fits the model and transforms the embeddings.

        Args:
            embeddings (np.ndarray): Embeddings to fit and transform.

        Returns:
            np.ndarray: Reduced embeddings.
        """
        if self.method == "UMAP":
            self.reducer = umap.UMAP(n_components=self.n_components, random_state=42)
            return self.reducer.fit_transform(embeddings)
        else:
            raise NotImplementedError(
                "fit_transform is only implemented for UMAP in this context."
            )
