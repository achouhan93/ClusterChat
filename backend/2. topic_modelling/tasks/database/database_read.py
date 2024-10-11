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
        index_name
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

    def fetch_embeddings(self, 
                         start_date,
                         end_date):
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
            "pubmed_bert_vector",
        ]

        search_params = {
            "sort": [{"articleDate": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "articleDate": {
                                    "gte": start_date,
                                    "lte": end_date,
                                }
                            }
                        }
                    ]
                }
            },
            "_source": fields_to_include,
        }

        # Execute the initial search request
        response = self.client.search(
            index=self.os_index_name,
            scroll="10m",
            size=5000,
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
                                    "articleDate": doc["_source"].get(
                                        "articleDate"
                                    ),
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
                        yield np.array(
                            embeddings_batch, dtype=np.float32
                        ), ids_batch
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
                f"Processing completed for the date range: {start_date} to {end_date}"
            )
