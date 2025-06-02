import logging
from typing import List, Dict, Any

# Configure logging
log = logging.getLogger(__name__)


def opensearch_existing_check(
    os_index: Any, index_name: str, id_list: List[str]
) -> List[str]:
    """
    Check for the non-existing documents in an OpenSearch index.

    Args:
        os_index (Any): An OpenSearch client instance capable of handling 'mget' requests.
        index_name (str): The name of the OpenSearch index to search in.
        id_list (List[str]): A list of document IDs to check for existence.

    Returns:
        List[str]: A list of document IDs that are not found in the given index.
    """
    # Prepare the request payload for the mget API
    id_docs = [{"_id": doc_id} for doc_id in id_list]
    non_existing = []

    if not id_docs:
        log.info("Empty ID list provided; returning empty result.")
        return non_existing

    try:
        # Perform a multi-get operation to check existence of documents
        response = os_index.mget(index=index_name, body={"docs": id_docs})

        # Extract the IDs that were not found in OpenSearch
        non_existing = [doc["_id"] for doc in response["docs"] if not doc["found"]]

        log.info(
            "Checked %d documents in index '%s'. %d documents not found.",
            len(id_list),
            index_name,
            len(non_existing),
        )

    except Exception as e:
        log.error("Error while checking document existence in OpenSearch: %s", str(e))
        raise

    return non_existing
