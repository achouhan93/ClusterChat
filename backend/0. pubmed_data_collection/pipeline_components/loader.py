from tqdm import tqdm
import logging
from pipeline_helpers.loader_helper.database_insert import opensearch_insert
import sys

log = logging.getLogger(__name__)


def loadArticles(index_connection, articleList, index_name):
    success = True

    try:
        opensearch_insert(index_connection, index_name[0], articleList)
    except Exception:
        success = False
        error_message = f"Failed to insert article, Check logs for more information \n"
        logging.error(error_message)
        print(error_message)  # Display to command line
        input("Press Enter to acknowledge the error and terminate the script...")
        sys.exit(1)
    return success
