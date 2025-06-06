"""
Module for fetching document embeddings from OpenSearch in batches.
"""

import logging
from typing import Generator, Tuple, List, Dict, Any
from datetime import date

import numpy as np
from tqdm import tqdm
from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    A class to fetch BERT-based embeddings from an OpenSearch index.

    Attributes:
        client (OpenSearch): OpenSearch client connection.
        os_index_name (str): Name of the OpenSearch index.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
    """

    def __init__(
        self,
        opensearch_connection: OpenSearch,
        index_name: str,
        start_date: str,
        end_date: str,
    ) -> None:
        """
        Initialize the DataFetcher with required configurations.

        Args:
            opensearch_connection (OpenSearch): OpenSearch client instance.
            index_name (str): Name of the index to query.
            start_date (str): Start date (inclusive) in 'YYYY-MM-DD' format.
            end_date (str): End date (inclusive) in 'YYYY-MM-DD' format.
        """
        self.client = opensearch_connection
        self.os_index_name = index_name
        self.start_date = start_date
        self.end_date = end_date

    def fetch_embeddings(
        self,
    ) -> Generator[Tuple[np.ndarray, List[Dict[str, Any]]], None, None]:
        """
        Fetch embeddings and associated metadata from OpenSearch in batches.

        Yields:
            Generator[Tuple[np.ndarray, List[Dict[str, Any]]]]:
                A tuple of (embeddings as a NumPy array, associated metadata).
        """
        fields_to_include = [
            "documentID",
            "articleDate",
            "title",
            "journal:title",
            "keywords:name",
            "meshTerms",
            "chemicals",
            "authors:name",
            "authors:affiliation",
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
                                    "gte": self.start_date,
                                    "lte": self.end_date,
                                }
                            }
                        }
                    ]
                }
            },
            "_source": fields_to_include,
        }

        try:
            # Execute the initial search request
            response = self.client.search(
                index=self.os_index_name,
                scroll="5m",
                size=1000,
                body=search_params,
            )

            # Get the scroll ID and hits from the initial search request
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]
            total_docs = response["hits"]["total"]["value"]  # Total number of documents

            logger.info(f"Total documents to process: {total_docs}")

            with tqdm(total=total_docs, desc="Fetching embeddings") as pbar:
                while hits:
                    embeddings_batch: List[np.ndarray] = []
                    ids_batch: List[Dict[str, Any]] = []

                    try:
                        logging.info(f"considered {len(hits)} documents for processing")

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
                                        "keywords:name": doc["_source"].get(
                                            "keywords:name"
                                        ),
                                        "meshTerms": doc["_source"].get("meshTerms"),
                                        "chemicals": doc["_source"].get("chemicals"),
                                        "authors:name": doc["_source"].get(
                                            "authors:name"
                                        ),
                                        "authors:affiliation": doc["_source"].get(
                                            "authors:affiliation"
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

            pbar.close()

        except Exception as e:
            logger.error("Initial OpenSearch query failed: %s", e)

        finally:
            try:
                self.client.clear_scroll(scroll_id=scroll_id)
            except Exception:
                logger.warning(
                    "Scroll context may have expired or been closed already."
                )

            logger.info(
                f"Processing completed for the date range: {self.start_date} to {self.end_date}"
            )
