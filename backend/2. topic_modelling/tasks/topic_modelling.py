from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from tqdm import tqdm
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.vectorizers import ClassTfidfTransformer

class TopicModeller:
    """Class to fetch embeddings from OpenSearch in batches."""

    def __init__(
        self,
        model_path
    ):
        """
        Initialize the DataFetcher.

        Args:
            opensearch_connection (OpenSearch): OpenSearch client connection.
            index_name (str): Name of the OpenSearch index.
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.
        """
        self.model_location = model_path
        self.model_paths = []
        
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
        

        for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings(start_date, end_date):
            embeddings_list.extend(embeddings_batch)
            documents_list.extend([doc['abstract_chunk'] for doc in ids_batch])
            document_ids_list.extend([doc['documentID'] for doc in ids_batch])
            document_date.extend([doc['articleDate'] for doc in ids_batch])
            document_title.extend([doc['title'] for doc in ids_batch])
            document_journal.extend([doc['journal:title'] for doc in ids_batch])
            document_mesh.extend([doc['meshTerms'] for doc in ids_batch])
            document_chemicals.extend([doc['chemicals'] for doc in ids_batch])
            document_authors.extend([doc['authors.name'] for doc in ids_batch])
            document_affiliations.extend([doc['authors.affiliation'] for doc in ids_batch])

        if not embeddings_list:
            return None  # No data to process for this date range

        embeddings = np.array(embeddings_list)
        texts = documents_list

        # Dimensionality reduction with UMAP to 50 dimensions
        umap_model = UMAP(
            n_neighbors=15,
            n_components=50, 
            min_dist=0.0, 
            metric='cosine',
            random_state=42
            )

        # Clustering with HDBSCAN
        hdbscan_model = HDBSCAN(
            min_cluster_size=15,
            metric='euclidean',
            cluster_selection_method='eom'
            )

        # Initialize BERTopic
        topic_model = BERTopic(
            embedding_model=None,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=None,
            ctfidf_model=None,
            representation_model=None,
            top_n_words=10,
            language='english',
            verbose=True,
            calculate_probabilities=False,
            nr_topics='auto',
            low_memory=True
        )

        # Fit the model
        topics, probs = topic_model.fit_transform(texts, embeddings)

        # Create a DataFrame to store document info
        doc_info = pd.DataFrame({
            'DocumentID': document_ids_list,
            'Document': documents_list,
            'Embedding': embeddings_list,
            'ArticleDate': document_date,
            'Title': document_title,
            'Journal': document_journal,
            'MeshTerms': document_mesh,
            'Chemicals': document_chemicals,
            'Authors': document_authors,
            'Topic': topics
        })

        # Store doc_info in the model
        topic_model.doc_info = doc_info

        # Save the model
        bertopic_model_path = f'bertopic_model_{start_date}_{end_date}.pkl'
        exact_model_path = self.model_location + bertopic_model_path
        topic_model.save(exact_model_path)

        self.model_paths.append(exact_model_path)
        
    def merge_bertopic_models(self):
        """
        Merges multiple BERTopic models into a single model.
        
        Args:
        model_paths (list): A list of file paths to the BERTopic models.
        
        Returns:
        BERTopic: A merged BERTopic model.
        """
        topic_models = [BERTopic.load(path) for path in self.model_paths]
        merged_model = BERTopic.merge_models(topic_models, min_similarity=0.9)

        merged_model.save(self.model_location+'merged_bertopic.pkl')

        return merged_model
    
    def apply_vectorizer_to_merged_model(self, merged_model):
        """
        Apply CountVectorizer and ClassTfidfTransformer to the merged BERTopic model.
        
        Args:
        merged_model (BERTopic): The merged BERTopic model.
        documents (list): A list of all documents to be used for vectorization.
        
        Returns:
        BERTopic: The updated BERTopic model with the vectorizer applied.
        """
        all_documents = [
            doc for model_path in self.model_paths 
            for doc in BERTopic.load(model_path).doc_info['Document'].tolist()
            ]
        
        # Initialize CountVectorizer and ClassTfidfTransformer
        vectorizer_model = CountVectorizer(stop_words='english')
        ctfidf_model = ClassTfidfTransformer(
            bm25_weighting=True,
            reduce_frequent_words=True
            )
        
        # Set the vectorizer and transformer to the model
        merged_model.vectorizer_model = vectorizer_model
        merged_model.ctfidf_model = ctfidf_model
        
        # Update topics with new vectorizer and transformer
        merged_model.update_topics(all_documents)
        merged_model.save(self.model_location+'final_bertopic_model.pkl')

        return merged_model