from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from tqdm import tqdm
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.representation import MaximalMarginalRelevance
import psutil
import os
import gc
import logging

log = logging.getLogger(__name__)


class TopicModeller:
    """Class to fetch embeddings from OpenSearch in batches."""

    def __init__(self, model_path):
        """
        Initialize the DataFetcher.

        Args:
            opensearch_connection (OpenSearch): OpenSearch client connection.
            index_name (str): Name of the OpenSearch index.
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.
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
        
        self.vectorizer_model = CountVectorizer(stop_words="english")
        self.ctfidf_model = ClassTfidfTransformer(
            bm25_weighting=True, reduce_frequent_words=True
        )

        # Representation model
        self.representation_model = MaximalMarginalRelevance(diversity=0.3)


    def _log_memory_usage(self):
        if psutil:
            mem = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)
            log.info(f"[Memory Usage] Current process memory: {mem:.2f} GB")

    def _write_model_path(self, path):
        with open(self.model_paths_file, "a") as f:
            f.write(path + "\n")


    def train_bertopic_model(self, date_range, data_fetcher):
        """
        Train a BERTopic model on documents within the given date range.

        Args:
            date_range (tuple): A tuple containing start and end dates.
            data_fetcher (DataFetcher): An instance of DataFetcher to fetch data.

        Returns:
            str: The file path where the BERTopic model is saved.
        """
        start_date, end_date = date_range

        # Fetch documents for the date range
        embeddings_list, documents_list, document_ids_list = [], [], []
        document_date, document_title, document_journal = [], [], []
        document_mesh, document_chemicals, document_authors = [], [], []
        document_affiliations = []

        try:
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
                return None  # No data to process for this date range

            embeddings = np.array(embeddings_list)
            texts = documents_list

            # Initialize BERTopic
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

            # Fit the model
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
            log.error(f"[Error] Failed {start_date} to {end_date}: {str(e)}")

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
                topic_model
            )
            gc.collect()
            self._log_memory_usage()