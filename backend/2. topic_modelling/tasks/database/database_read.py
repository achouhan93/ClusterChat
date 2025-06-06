"""
Module for fetching embeddings from OpenSearch.
"""

import logging
from typing import Generator, List, Tuple, Dict, Any
from datetime import date
import numpy as np
from tqdm import tqdm

# Constants
CONST_EUTILS_DEFAULT_MINDATE = "1800-01-01"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y-%m-%d")

# Configure module-level logger
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Class to fetch document embeddings and metadata from OpenSearch in batches.
    """

    def __init__(self, opensearch_connection: Any, index_name: str) -> None:
        """
        Initialize the DataFetcher with an OpenSearch connection and index name.

        Args:
            opensearch_connection (Any): OpenSearch client instance.
            index_name (str): Name of the OpenSearch index to query.
        """
        self.client = opensearch_connection
        self.os_index_name = index_name

    def fetch_embeddings(
        self, start_date: str, end_date: str
    ) -> Generator[Tuple[np.ndarray, List[Dict[str, Any]]], None, None]:
        """
        Generator that yields batches of embeddings and their associated metadata.

        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.

        Yields:
            Tuple[np.ndarray, List[Dict[str, Any]]]: A tuple containing:
                - NumPy array of embedding vectors.
                - List of metadata dictionaries for corresponding documents.
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

        try:
            # Execute the initial search request
            response = self.client.search(
                index=self.os_index_name,
                scroll="10m",
                size=5000,
                body=search_params,
            )
        except Exception as e:
            logger.error(f"Initial OpenSearch search query failed: {str(e)}")
            return

        scroll_id: str = response.get("_scroll_id", "")
        hits: List[Dict[str, Any]] = response["hits"]["hits"]
        total_docs: int = response["hits"]["total"]["value"]

        with tqdm(total=total_docs, desc="Fetching documents") as pbar:
            while hits:
                embeddings_batch: List[List[float]] = []
                ids_batch: List[Dict[str, Any]] = []

                try:
                    logger.info(f"Considered {len(hits)} documents for processing")

                    for doc in tqdm(hits, leave=False, desc="Processing batch"):
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
                                    "authors.name": doc["_source"].get("authors:name"),
                                    "authors.affiliation": doc["_source"].get(
                                        "authors:affiliation"
                                    ),
                                    "abstract_chunk": doc["_source"].get(
                                        "abstract_chunk"
                                    ),
                                }
                            )

                    if embeddings_batch:
                        yield np.array(embeddings_batch, dtype=np.float32), ids_batch
                    else:
                        logger.warning("No embeddings found in the current batch.")

                except Exception as e:
                    logger.error(
                        f"Error during vector create and storage operation due to error {e}"
                    )

                pbar.update(len(hits))

                try:
                    # Paginate through the search results using the scroll parameter
                    response = self.client.scroll(scroll_id=scroll_id, scroll="10m")
                    hits = response["hits"]["hits"]
                    scroll_id = response.get("_scroll_id", "")
                except Exception as e:
                    logger.error(f"Error during OpenSearch scroll: {str(e)}")
                    break

            try:
                # Clear the scroll
                self.client.clear_scroll(scroll_id=scroll_id)
                logger.info("Scroll context cleared.")
            except Exception as e:
                logger.warning(f"Failed to clear scroll context: {str(e)}")

            pbar.close()
            logger.info(
                f"Completed fetching embeddings for date range {start_date} to {end_date}."
            )
