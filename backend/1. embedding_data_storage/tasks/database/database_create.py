import logging
from typing import Any, Dict

from opensearchpy import OpenSearch

# Configure module-level logger
logger = logging.getLogger(__name__)


def opensearch_create(
    os_connection: OpenSearch, index_name: str, os_mapping: Dict[str, Any]
) -> None:
    """
    Creates an OpenSearch index if it does not already exist.

    Args:
        os_connection (OpenSearch): OpenSearch client connection.
        index_name (str): Name of the index to create.
        os_mapping (Dict[str, Any]): Mapping definition for the index.

    Returns:
        None

    Notes:
        - If the index already exists, no action is taken.
        - If creation is attempted, HTTP 400/404 errors are ignored.
    """
    try:
        index_exists = os_connection.indices.exists(index=index_name)

        if not index_exists:
            logger.info(f"Index {index_name} does not exist. Creating index...")
            os_connection.indices.create(
                index=index_name, body=os_mapping, ignore=[400, 404]
            )
            logger.info(f"Index {index_name} created successfully.")
        else:
            logger.info(f"Index {index_name} already exists. Skipping creation.")

    except Exception as e:
        logger.exception(f"Error while creating index {index_name}: {str(e)}")
        raise
