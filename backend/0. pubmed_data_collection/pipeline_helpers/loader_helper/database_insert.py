import logging
import sys
from typing import List, Dict, Any
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from tqdm import tqdm

# Configure logging
log = logging.getLogger(__name__)

# Constants
BATCH_SIZE: int = 50


def opensearch_insert(
    os_index: OpenSearch, index_name: str, articles: List[Dict[str, Any]]
) -> None:
    """
    Inserts a batch of documents into an OpenSearch index.

    Args:
        os_index (OpenSearch): OpenSearch client instance.
        index_name (str): The name of the index to insert documents into.
        articles (List[Dict[str, Any]]): A list of article metadata in JSON format.

    Returns:
        None

    Notes:
        Each document is uniquely identified by its 'PMID'.
        Documents are inserted in batches using OpenSearch bulk helper.
        Failed insertions are logged.
    """
    bulk_data = []  # List to store bulk actions
    failed_ids = []  # List to store IDs of failed inserts

    for articleInformation in tqdm(articles, desc="Preparing bulk document insert"):
        # Create document dictionary based on the articleInformation
        doc = {
            "_op_type": "index",
            "_index": index_name,
            "_id": articleInformation["PMID"],  # Use PMID as the document ID
            "_source": {
                "title": (
                    "NONE"
                    if articleInformation["Title"] is None
                    else articleInformation["Title"]
                ),
                "vernacularTitle": (
                    "NONE"
                    if articleInformation["VernacularTitle"] is None
                    else articleInformation["VernacularTitle"]
                ),
                "abstract": (
                    "no abstract available on pubmed"
                    if articleInformation["Abstract"] is None
                    else articleInformation["Abstract"]
                ),
                "otherAbstract": (
                    "NONE"
                    if articleInformation["OtherAbstract"] is None
                    else articleInformation["OtherAbstract"]
                ),
                "language": articleInformation["Language"],
                "status": articleInformation["Status"],
                "articleDate": articleInformation["ArticleDate"],
                "history": [
                    {"date": article["Date"], "type": article["Type"]}
                    for article in articleInformation["History"]
                ],
                "authors": [
                    {
                        "firstName": author["ForeName"],
                        "lastName": author["LastName"],
                        "affiliations": [
                            {
                                "institute": (
                                    "NONE"
                                    if affiliation["Institute"] is None
                                    else affiliation["Institute"]
                                )
                            }
                            for affiliation in author["Affiliations"]
                        ]
                        or [{"institute": "NONE"}],
                    }
                    for author in articleInformation["Authors"]
                ],
                "grants": [
                    {
                        "grantID": grant["ResearchGrantID"],
                        "acronym": grant["Acronym"],
                        "agency": grant["Agency"],
                        "country": grant["Country"],
                    }
                    for grant in articleInformation["Grants"]
                ],
                "chemicals": [
                    {
                        "chemicalMeshID": chemical["MeshUI"],
                        "name": (
                            "NONE" if chemical["Name"] is None else chemical["Name"]
                        ),
                    }
                    for chemical in articleInformation["Chemicals"]
                ],
                "keywords": [
                    {
                        "name": "NONE" if keyword["Name"] is None else keyword["Name"],
                        "major": keyword["Major"],
                    }
                    for keyword in articleInformation["Keywords"]
                ],
                "meshTerms": [
                    {
                        "meshID": mesh["MeshUI"],
                        "name": "NONE" if mesh["Name"] is None else mesh["Name"],
                        "major": mesh["Major"],
                    }
                    for mesh in articleInformation["MeshTerms"]
                ],
                "publicationTypes": [
                    {
                        "publicationMeshID": publication["MeshUI"],
                        "type": publication["Name"],
                    }
                    for publication in articleInformation["PublicationTypes"]
                ],
                "journalInformation": {
                    "journalTitle": articleInformation["JournalInformation"][
                        "JournalTitle"
                    ],
                    "abbreviation": articleInformation["JournalInformation"][
                        "Abbreviation"
                    ],
                    "journalIssueInformation": {
                        "medium": articleInformation["JournalInformation"][
                            "JournalIssue"
                        ]["JournalIssueMedium"],
                        "volume": articleInformation["JournalInformation"][
                            "JournalIssue"
                        ]["JournalVolume"],
                        "issueNumber": articleInformation["JournalInformation"][
                            "JournalIssue"
                        ]["JournalIssueNumber"],
                        "issueDate": {
                            "year": articleInformation["JournalInformation"][
                                "JournalIssue"
                            ]["JournalIssueDate"]["year"],
                            "month": articleInformation["JournalInformation"][
                                "JournalIssue"
                            ]["JournalIssueDate"]["month"],
                            "day": articleInformation["JournalInformation"][
                                "JournalIssue"
                            ]["JournalIssueDate"]["day"],
                        },
                    },
                },
                "fullTextURL": articleInformation["FullTextURL"],
                "fullText": articleInformation["FullText"],
                "vectorisedFlag": articleInformation["VectorisedFlag"],
                "nlpProcessedFlag": articleInformation["NLPProcessedFlag"],
            },
        }
        bulk_data.append(doc)  # Append the action to the bulk data list

        if len(bulk_data) >= BATCH_SIZE:
            failed_ids.extend(process_bulk(os_index, bulk_data, index_name))
            bulk_data = []  # Reset bulk data list after attempting to insert

    # Process any remaining documents
    if bulk_data:
        failed_ids.extend(process_bulk(os_index, bulk_data, index_name))

    # Log all failed IDs after processing is complete
    if failed_ids:
        log.error(f"Failed to insert articles with IDs: {failed_ids}")

    del bulk_data
    del failed_ids
    os_index.indices.refresh(index=index_name)


def process_bulk(
    os_index: OpenSearch, bulk_data: List[Dict[str, Any]], index_name: str
) -> List[str]:
    """
    Executes a bulk insert operation and returns a list of failed document IDs.

    Args:
        os_index (OpenSearch): OpenSearch client instance.
        bulk_data (List[Dict[str, Any]]): List of documents for bulk insertion.
        index_name (str): Target index name.

    Returns:
        List[str]: List of document IDs that failed to insert.
    """
    failed_ids = []
    try:
        response = bulk(
            os_index, bulk_data, index=index_name, raise_on_error=False, refresh=False
        )

        for resp, doc in zip(
            response[1], bulk_data
        ):  # responses[1] should contain item responses
            if (
                resp["index"]["status"] != 201 and resp["index"]["status"] != 200
            ):  # 201 Created, 200 OK
                failed_ids.append(doc["_id"])
                logging.error(
                    f"Failed to insert article with id: {doc['_id']}, reason: {resp['index']['error']}"
                )
    except Exception as e:
        error_message = f"General bulk insert error: {str(e)}"
        log.error(error_message)  # Log to file
        print(error_message)  # Display to command line
        input("Press Enter to acknowledge the error and terminate the script...")
        sys.exit(1)  # Exit the script with a non-zero exit code

    return failed_ids
