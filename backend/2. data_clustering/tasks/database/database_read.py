"""
Module for fetching embeddings from OpenSearch.
"""

import numpy as np
import logging
from tqdm import tqdm
from datetime import timedelta, datetime, date

CONST_EUTILS_DEFAULT_MINDATE = "1800-01-01"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y-%m-%d")

class DataFetcher:
    """Class to fetch embeddings from OpenSearch in batches."""

    def __init__(
        self,
        opensearch_connection,
        index_name,
        start_date=None,
        end_date=None,
    ):
        """
        Initialize the DataFetcher.

        Args:
            opensearch_connection (OpenSearch): OpenSearch client connection.
            index_name (str): Name of the OpenSearch index.
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.
        """
        self.client = opensearch_connection
        self.os_index_name = index_name
        
        # Parse dates
        if start_date and end_date:
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            self.start_date = datetime.strptime(CONST_EUTILS_DEFAULT_MINDATE, "%Y-%m-%d")
            self.end_date = datetime.strptime(CONST_EUTILS_DEFAULT_MAXDATE, "%Y-%m-%d")

        # Initialize current_date for iteration
        self.current_date = self.end_date

    def fetch_embeddings(self):
        """
        Generator function to fetch embeddings from OpenSearch in batches.

        Yields:
            tuple: A tuple containing a batch of embeddings and their corresponding IDs.
        """
        fields_to_include = [
            "documentID", 
            "articleDate",
            "title", 
            "journal:title",
            "meshTerms",
            "chemicals",
            "authors.name",
            "authors.affiliation",
            "abstract_chunk",
            "pubmed_bert_vector"
        ]

        while self.current_date >= self.start_date:
            max_date = self.current_date.strftime("%Y-%m-%d")
            date_offset = self.current_date - timedelta(days=0)
            min_date = date_offset.strftime("%Y-%m-%d")
        
            search_params = {
                "sort": [
                    {
                        "articleDate": {
                            "order": "desc"
                            }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "articleDate": {
                                        "gte": min_date, 
                                        "lte": max_date,
                                        }
                                    }
                            }
                            ]
                    }
                },
                "_source": fields_to_include
            }

            # Execute the initial search request
            response = self.client.search(
                index=self.os_index_name,
                scroll="10m",
                size=1000,
                body=search_params,
            )

            # Get the scroll ID and hits from the initial search request
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]
            total_docs = response["hits"]["total"]["value"]  # Total number of documents

            with tqdm(total=total_docs) as pbar:
                while hits:
                    try:
                        logging.info(f"considered {len(hits)} documents for processing")
                        embeddings_batch = []
                        ids_batch = []

                        for doc in tqdm(hits):
                            embedding = doc["_source"].get("pubmed_bert_vector")
                            if embedding:
                                embeddings_batch.append(embedding)
                                ids_batch.append(
                                    {
                                        "documentID": doc["_source"].get("documentID"),
                                        "articleDate": doc["_source"].get("articleDate"),
                                        "title": doc["_source"].get("title"),
                                        "journal:title": doc["_source"].get(
                                            "journal:title"
                                        ),
                                        "meshTerms": doc["_source"].get("meshTerms"),
                                        "chemicals": doc["_source"].get("chemicals"),
                                        "authors.name": doc["_source"].get(
                                            "authors.name"
                                        ),
                                        "authors.affiliation": doc["_source"].get(
                                            "authors.affiliation"
                                        ),
                                        "abstract_chunk": doc["_source"].get(
                                            "abstract_chunk"
                                        ),
                                    }
                                )

                        if embeddings_batch:
                            yield np.array(embeddings_batch, dtype=np.float32), ids_batch
                        else:
                            logging.warning("No embeddings found in the current batch.")
                    
                    except Exception as e:
                        logging.error(
                            f"Error during vector create and storage operation due to error {e}"
                        )

                    pbar.update(len(hits))

                    # Paginate through the search results using the scroll parameter
                    response = self.client.scroll(scroll_id=scroll_id, scroll="10m")
                    hits = response["hits"]["hits"]
                    scroll_id = response["_scroll_id"]
            
                # Clear the scroll
                self.client.clear_scroll(scroll_id=scroll_id)
                pbar.close()
                logging.info(
                    f"Processing completed for the date range: {min_date} to {max_date}"
                )

                # Move to the previous day
                self.current_date -= timedelta(days=1)
            
        logging.info(
            f"Processing completed for all documents in the date range "
            f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}."
        )
                