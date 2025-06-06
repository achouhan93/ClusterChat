import logging
from typing import List, Tuple, Dict, Any
from tqdm import tqdm
from opensearchpy import OpenSearch

# Configure logger
logger = logging.getLogger(__name__)


def opensearch_insert(
    os_connection: OpenSearch,
    index_name: str,
    document_details: List[Tuple[str, List[float], Dict[str, Any]]],
    batch_size: int = 1000,
) -> bool:
    """
    Inserts documents into an OpenSearch index in batches.

    Args:
        os_connection (OpenSearch): OpenSearch client connection.
        index_name (str): The target OpenSearch index.
        document_details (List[Tuple[str, List[float], Dict[str, Any]]]):
            List of tuples where each tuple contains:
            - document ID (str)
            - embedding vector (List[float])
            - metadata dictionary (Dict[str, Any])
        batch_size (int, optional): Number of documents to index per batch. Defaults to 1000.

    Returns:
        bool: True if all batches are successfully indexed; False otherwise.
    """
    success: bool = True
    total_docs: int = len(document_details)

    # Split the document details into batches of size `batch_size`
    for start in tqdm(
        range(0, total_docs, batch_size), desc="Saving document in database"
    ):
        actions: List[Dict[str, Any]] = []
        batch = document_details[start : start + batch_size]

        for doc_id, embedding, metadata in tqdm(
            batch, leave=False, desc="Preparing batch"
        ):
            # Define the indexing action
            action = {"index": {"_index": index_name, "_id": doc_id}}
            doc = {
                "documentSource": metadata.get("document_source"),
                "documentID": metadata.get("pubmed_id"),
                "articleDate": metadata.get("articleDate"),
                "title": metadata.get("title"),
                "journal:title": metadata.get("journalTitle"),
                "keywords:name": metadata.get("keywords"),
                "meshTerms": metadata.get("meshTerms"),
                "meshIds": metadata.get("meshIds"),
                "chemicals": metadata.get("chemicals"),
                "authors:name": metadata.get("authorNames"),
                "authors:affiliation": metadata.get("authorAffiliations"),
                "abstract_chunk_id": metadata.get("text_chunk_id"),
                "abstract_chunk": metadata.get("pubmed_text"),
                "pubmed_bert_vector": embedding,
            }
            actions.append(action)
            actions.append(doc)
        try:
            os_connection.bulk(index=index_name, body=actions)
            logger.info(
                f"Successfully indexed batch {start // batch_size + 1} ({len(batch)} documents)."
            )
        except Exception as e:
            logging.error(
                f"Bulk Indexing failed for batch {start//batch_size+1} due to error: {str(e)}"
            )
            success = False

    return success
