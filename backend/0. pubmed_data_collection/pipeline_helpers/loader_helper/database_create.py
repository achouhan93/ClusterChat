import logging
from typing import Any, Dict

# Configure logging
log = logging.getLogger(__name__)


def opensearch_create(
    os_index: Any, index_name: str, os_mapping: Dict[str, Any]
) -> None:
    """
    Create an OpenSearch index if it does not already exist.

    Args:
        os_index (Any): OpenSearch client instance with an `indices` attribute.
        index_name (str): The name of the index to be created.
        os_mapping (Dict[str, Any]): The mapping configuration for the index.

    Returns:
        None

    Notes:
        - If the index already exists, no action is taken.
        - If the index does not exist, it will be created with the specified mapping.
    """
    try:
        if not os_index.indices.exists(index=index_name):
            log.info("Index '%s' does not exist. Creating index...", index_name)
            os_index.indices.create(
                index=index_name, ignore=[400, 404], body=os_mapping
            )
            log.info("Index '%s' created successfully.", index_name)
        else:
            log.info("Index '%s' already exists. Skipping creation.", index_name)
    except Exception as e:
        log.error("Failed to create index '%s': %s", index_name, str(e))
        raise
