import logging
import time
import requests
import xml.etree.ElementTree as ET
from datetime import date
from typing import List

from tqdm import tqdm
import utils
from pipeline_helpers.extractor_helpers.extractor_utils import opensearch_existing_check

# Configuration and Constants
CONFIG = utils.load_config_from_env()
CONST_EUTILS_MAX_ARTICLES = 10_000_000
CONST_EUTILS_DEFAULT_MINDATE = "1900"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y/%m/%d")
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

EFETCH_UTILITY = "efetch.fcgi"
ESEARCH_UTILITY = "esearch.fcgi"

log = logging.getLogger(__name__)


def extract_articles_data(database: str, ids: str) -> str:
    """
    Fetches XML data for articles from the NCBI E-utilities 'efetch' endpoint.

    Args:
        database (str): The NCBI database name (e.g., 'pubmed').
        ids (str): Comma-separated list of article IDs.

    Returns:
        str: Raw XML content returned from the API.
    """

    ARGS = {"db": database, "retmode": "xml", "id": ids}

    try:
        response = requests.get(f"{BASE_URL}/{EFETCH_UTILITY}", params=ARGS)
        response.raise_for_status()
        return response.text
    except Exception as e:
        log.error(f"API call failed while fetching article data: {e}")
        raise


def get_article_ids_for_time_range(
    database: str, mindate: str, maxdate: str, database_connection
) -> List[str]:
    """
    Retrieves article IDs from the NCBI E-utilities 'esearch' endpoint within a date range.

    Args:
        database (str): The NCBI database name (e.g., 'pubmed').
        mindate (str): Start date (format: YYYY/MM/DD).
        maxdate (str): End date (format: YYYY/MM/DD).
        database_connection: Connection object to access OpenSearch for existence checks.

    Returns:
        List[str]: List of new article IDs not found in the OpenSearch index.
    """
    all_ids = []
    max_retries = 3  # Number of retries
    retry_delay = 5  # Delay between retries in seconds

    # The publication date reflects the date on which the article was first made available
    # to the public, and is therefore the most relevant date for users who are
    # interested in the currency of the research.

    params = {
        "db": database,
        "mindate": mindate,
        "maxdate": maxdate,
        "retmode": "xml",
        "datetype": "pdat",
        "retmax": str(CONST_EUTILS_MAX_ARTICLES),
        "usehistory": "y",
    }

    # The modification date (mdat), on the other hand, reflects the date on which the article
    # was last modified or updated, which may not be as useful for users who are interested
    # in recent research. Similarly, the Entrez date (edat) reflects the date on which the article
    # was added to the PubMed database, which may not necessarily correspond to the
    # publication date.

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(f"{BASE_URL}/{ESEARCH_UTILITY}", params=params)
            response.raise_for_status()  # Raise HTTP errors
            tree = ET.fromstring(response.text)
            total_count = int(tree.find(".//Count").text)

            log.info(f"Found {total_count} new articles from {mindate} to {maxdate}")

            if total_count >= 10000:
                webenv = tree.find(".//WebEnv").text
                query_key = tree.find(".//QueryKey").text
                batch_size = 1000  # number of records to retrieve per batch

                for retstart in tqdm(
                    range(0, total_count, batch_size), desc="Fetching records"
                ):
                    fetch_params = {
                        "db": database,
                        "WebEnv": webenv,
                        "query_key": query_key,
                        "retmode": "xml",
                        "retstart": retstart,
                        "retmax": batch_size,
                    }

                    for fetch_attempt in range(1, max_retries + 1):
                        try:
                            fetch_response = requests.get(
                                f"{BASE_URL}/{EFETCH_UTILITY}", params=fetch_params
                            )
                            fetch_response.raise_for_status()  # Raise HTTP errors
                            ids = get_ids_from_xml_for_time_range(
                                fetch_response.text, database_connection
                            )
                            all_ids.extend(ids)
                            break  # Exit retry loop on success
                        except Exception as fetch_err:
                            log.error(
                                f"Fetch attempt {fetch_attempt} failed: {fetch_err}"
                            )
                            if fetch_attempt < max_retries:
                                log.info(f"Retrying in {retry_delay} seconds...")
                                time.sleep(retry_delay)
                            else:
                                log.error(
                                    "Max fetch retries reached. Stopping execution."
                                )
                                raise RuntimeError(
                                    "Failed to fetch batch data after multiple retries"
                                ) from fetch_err

                    time.sleep(1)

            else:
                all_ids = get_ids_from_xml(response.text, database_connection)

            break  # Exit retry loop on success

        except Exception as e:
            log.error(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                log.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                log.error("Max retries reached. Stopping execution.")
                raise RuntimeError("Failed to fetch data after multiple retries") from e

    return all_ids


def get_ids_from_xml(xml_content: str, os_connection) -> List[str]:
    """
    Parses XML content and filters out already indexed article IDs.

    Args:
        xml_content (str): XML response from NCBI.
        os_connection: OpenSearch client connection object.

    Returns:
        List[str]: List of new article IDs not present in the index.
    """
    try:
        tree = ET.fromstring(xml_content)
        ids = [elem.text for elem in tree.findall(".//Id") if elem.text]
        index_name = CONFIG["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]

        return opensearch_existing_check(os_connection, index_name, ids)
    except Exception as e:
        log.error(f"Error parsing XML for IDs: {e}")
        raise


def get_ids_from_xml_for_time_range(xml_content: str, os_connection) -> List[str]:
    """
    Parses article XML to extract PMIDs and filters out already indexed ones.

    Args:
        xml_content (str): XML content from efetch endpoint.
        os_connection: OpenSearch client connection object.

    Returns:
        List[str]: Filtered list of new PMIDs.
    """
    try:
        tree = ET.fromstring(xml_content)
        pubmed_articles = tree.findall(".//PubmedArticle")
        ids = [
            article.find(".//PMID").text
            for article in pubmed_articles
            if article.find(".//PMID") is not None
        ]
        index_name = CONFIG["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]

        return opensearch_existing_check(os_connection, index_name, ids)
    except Exception as e:
        log.error(f"Error parsing XML for IDs: {e}")
        raise
