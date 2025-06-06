import os
import gc
import psutil
import logging
from time import sleep
from typing import Optional, Tuple, Any

import numpy as np
import pandas as pd
from tqdm import tqdm
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.representation import MaximalMarginalRelevance

# Configure logger
logger = logging.getLogger(__name__)


class TopicModeller:
    """
    A class to train BERTopic models on embedding batches retrieved via a DataFetcher.

    The model uses UMAP for dimensionality reduction and HDBSCAN for clustering.
    """

    def __init__(self, model_path: str) -> None:
        """
        Initialize the TopicModeller.

        Args:
            model_path (str): Directory path where models and logs will be saved.
        """
        self.model_location = model_path
        os.makedirs(self.model_location, exist_ok=True)
        self.model_paths_file = os.path.join(self.model_location, "model_paths.txt")

        # Dimensionality reduction with UMAP to 50 dimensions
        self.umap_model = UMAP(
            n_components=50, min_dist=0.0, metric="cosine", random_state=42
        )

        # Clustering with HDBSCAN
        self.hdbscan_model = HDBSCAN(
            min_cluster_size=15, metric="euclidean", cluster_selection_method="eom"
        )

        # Vectorization and topic representation
        self.vectorizer_model = CountVectorizer(stop_words="english")
        self.ctfidf_model = ClassTfidfTransformer(
            bm25_weighting=True, reduce_frequent_words=True
        )

        # Representation model
        self.representation_model = MaximalMarginalRelevance(diversity=0.3)

    def _log_memory_usage(self) -> None:
        """Logs the current memory usage of the Python process."""
        if psutil:
            mem = psutil.Process(os.getpid()).memory_info().rss / (1024**3)
            logger.info(f"[Memory Usage] Current process memory: {mem:.2f} GB")

    def _write_model_path(self, path: str) -> None:
        """
        Appends the given model path to a persistent file.

        Args:
            path (str): The full path of the saved BERTopic model.
        """
        with open(self.model_paths_file, "a") as f:
            f.write(path + "\n")

    def train_bertopic_model(
        self, date_range: Tuple[str, str], data_fetcher: Any
    ) -> None:
        """
        Trains a BERTopic model on the embeddings for the specified date range.

        Args:
            date_range (Tuple[str, str]): Tuple of start and end dates (YYYY-MM-DD).
            data_fetcher (Any): Instance of a DataFetcher class that yields (embeddings, metadata).

        Returns:
            Optional[str]: File path of the saved BERTopic model, or None if training failed.
        """
        start_date, end_date = date_range

        # Storage for data
        embeddings_list, documents_list, document_ids_list = [], [], []
        document_date, document_title, document_journal = [], [], []
        document_mesh, document_chemicals, document_authors = [], [], []
        document_affiliations = []

        try:
            logger.info(f"Fetching data from {start_date} to {end_date}")
            for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings(
                start_date, end_date
            ):
                embeddings_list.extend(embeddings_batch)
                documents_list.extend([doc["abstract_chunk"] for doc in ids_batch])
                document_ids_list.extend([doc["documentID"] for doc in ids_batch])
                document_date.extend([doc["articleDate"] for doc in ids_batch])
                document_title.extend([doc["title"] for doc in ids_batch])
                document_journal.extend([doc["journal:title"] for doc in ids_batch])
                document_mesh.extend([doc["meshTerms"] for doc in ids_batch])
                document_chemicals.extend([doc["chemicals"] for doc in ids_batch])
                document_authors.extend([doc["authors.name"] for doc in ids_batch])
                document_affiliations.extend(
                    [doc["authors.affiliation"] for doc in ids_batch]
                )

            if not embeddings_list:
                logger.warning(
                    f"No embeddings found for the range {start_date} to {end_date}"
                )
                return None  # No data to process for this date range

            embeddings = np.array(embeddings_list)
            texts = documents_list

            logger.info("Initializing BERTopic model...")

            topic_model = BERTopic(
                embedding_model=None,
                umap_model=self.umap_model,
                hdbscan_model=self.hdbscan_model,
                vectorizer_model=self.vectorizer_model,
                ctfidf_model=self.ctfidf_model,
                representation_model=self.representation_model,
                top_n_words=10,
                language="english",
                verbose=True,
                calculate_probabilities=False,
                nr_topics="auto",
                low_memory=True,
            )

            # Train the model
            logger.info("Training BERTopic model...")
            topics, _ = topic_model.fit_transform(texts, embeddings)

            # Create a DataFrame to store document info
            doc_info = pd.DataFrame(
                {
                    "DocumentID": document_ids_list,
                    "Document": documents_list,
                    "Embedding": embeddings_list,
                    "ArticleDate": document_date,
                    "Title": document_title,
                    "Journal": document_journal,
                    "MeshTerms": document_mesh,
                    "Chemicals": document_chemicals,
                    "Authors": document_authors,
                    "Topic": topics,
                }
            )

            # Store doc_info in the model
            topic_model.doc_info = doc_info

            # Save the model
            bertopic_model_path = f"bertopic_model_{start_date}_{end_date}.pkl"
            exact_model_path = os.path.join(self.model_location, bertopic_model_path)
            topic_model.save(exact_model_path)

            self._write_model_path(exact_model_path)
            self._log_memory_usage()

        except Exception as e:
            logger.error(f"[Error] Failed {start_date} to {end_date}: {str(e)}")

        finally:
            # Explicit memory cleanup
            del (
                embeddings_list,
                documents_list,
                document_ids_list,
                document_date,
                document_title,
                document_journal,
                document_mesh,
                document_chemicals,
                document_authors,
                document_affiliations,
                embeddings,
                texts,
                doc_info,
                topic_model,
            )
            gc.collect()
            sleep(2)
            self._log_memory_usage()
