import sys
import logging
from typing import List, Any

from pipeline_helpers.loader_helper.database_insert import opensearch_insert

log = logging.getLogger(__name__)


def load_articles(
    index_connection: Any, articleList: List[dict], index_name: List[str]
) -> bool:
    """
    Inserts a list of articles into an OpenSearch index.

    Args:
        index_connection (Any): OpenSearch client or connection object.
        article_list (List[dict]): List of article records to be inserted.
        index_name (List[str]): A list containing a single string, the name of the OpenSearch index.

    Returns:
        bool: True if insertion was successful, False otherwise.

    Notes:
        On failure, logs the error, prints a message to the console,
        prompts for user acknowledgement, and exits the script.
    """
    try:
        opensearch_insert(index_connection, index_name[0], articleList)
        return True
    except Exception as e:
        error_message = (
            "Failed to insert article into OpenSearch. "
            "Check logs for more information."
        )
        log.error(f"{error_message} Exception: {e}")
        print(error_message)  # Display to command line
        input("Press Enter to acknowledge the error and terminate the script...")
        sys.exit(1)
