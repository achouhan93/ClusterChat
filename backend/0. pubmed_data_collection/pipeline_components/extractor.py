import requests
from datetime import date
import logging
import time
import utils
from tqdm import tqdm

import xml.etree.ElementTree as ET
from pipeline_helpers.extractor_helpers.extractor_utils import opensearch_existing_check

CONFIG = utils.load_config_from_env()
CONST_EUTILS_MAX_ARTICLES = 10000000
CONST_EUTILS_DEFAULT_MINDATE = "1900"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y/%m/%d")
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

EFETCH_UTILITY = "efetch.fcgi"
ESEARCH_UTILITY = "esearch.fcgi"

log = logging.getLogger(__name__)


def extractArticlesData(database, ids):

    ARGS = {"db": database, "retmode": "xml", "id": ids}

    try:
        response = requests.get(f"{BASE_URL}/{EFETCH_UTILITY}", params=ARGS)
        xml_file = response.text
    except Exception as e:
        log.error(f"ERROR: API call failed: {e}")

    return xml_file


def getArticleIdsForTimeRange(database, mindate, maxdate, database_connection):
    allids = []
    MAX_RETRIES = 3  # Number of retries
    RETRY_DELAY = 5  # Delay between retries in seconds

    # The publication date reflects the date on which the article was first made available
    # to the public, and is therefore the most relevant date for users who are
    # interested in the currency of the research.

    ARGS = {
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

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(f"{BASE_URL}/{ESEARCH_UTILITY}", params=ARGS)
            response.raise_for_status()  # Raise HTTP errors
            tree = ET.fromstring(response.text)
            total_count = int(tree.find(".//Count").text)

            log.info(
                f"Found {total_count} new articles for Date: {mindate} to {maxdate}"
            )

            if total_count >= 10000:
                webenv = tree.find(".//WebEnv").text
                query_key = tree.find(".//QueryKey").text

                # Retrieve the records in batches
                retmax = 1000  # number of records to retrieve per batch

                for retstart in tqdm(
                    range(0, total_count, retmax), desc="Fetching records"
                ):
                    fetch_ARGS = {
                        "db": database,
                        "WebEnv": webenv,
                        "query_key": query_key,
                        "retmode": "xml",
                        "retstart": retstart,
                        "retmax": retmax,
                    }

                    for fetch_attempt in range(1, MAX_RETRIES + 1):
                        try:
                            fetch_response = requests.get(
                                f"{BASE_URL}/{EFETCH_UTILITY}", params=fetch_ARGS
                            )
                            fetch_response.raise_for_status()  # Raise HTTP errors
                            ids = getIdsFromXMLForTimeRange(
                                fetch_response.text, database_connection
                            )
                            allids.extend(ids)
                            break  # Exit retry loop on success
                        except Exception as fetch_e:
                            log.error(
                                f"Fetch attempt {fetch_attempt} failed: {fetch_e}"
                            )
                            if fetch_attempt < MAX_RETRIES:
                                log.info(f"Retrying in {RETRY_DELAY} seconds...")
                                time.sleep(RETRY_DELAY)
                            else:
                                log.error(
                                    "Max fetch retries reached. Stopping execution."
                                )
                                raise RuntimeError(
                                    "Failed to fetch batch data after multiple retries"
                                ) from fetch_e

                    time.sleep(1)

            else:
                allids = getIdsFromXML(response.text, database_connection)

            break  # Exit retry loop on success

        except Exception as e:
            log.error(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                log.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                log.error("Max retries reached. Stopping execution.")
                raise RuntimeError("Failed to fetch data after multiple retries") from e

    return allids


def getIdsFromXML(xmlObject, os):
    try:
        tree = ET.fromstring(xmlObject)
        x_ids = tree.findall(".//Id")
        ids = [i.text for i in x_ids]

        index_name = CONFIG["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]
        non_existing_ids = opensearch_existing_check(os, index_name, ids)

        return non_existing_ids
    except Exception as e:
        log.error(f"Error parsing XML for IDs: {e}")
        raise


def getIdsFromXMLForTimeRange(xmlObject, os):
    try:
        tree = ET.fromstring(xmlObject)
        pubmed_articles = tree.findall(".//PubmedArticle")
        ids = [i.find(".//PMID").text for i in pubmed_articles]

        index_name = CONFIG["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]
        non_existing_ids = opensearch_existing_check(os, index_name, ids)

        return non_existing_ids
    except Exception as e:
        log.error(f"Error parsing XML for IDs: {e}")
        raise
