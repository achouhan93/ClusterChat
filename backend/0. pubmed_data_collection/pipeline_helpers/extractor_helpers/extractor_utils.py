import logging

log = logging.getLogger(__name__)


def opensearch_existing_check(os_index, index_name, id_list):
    # """"""""""
    # Functionality: Check if the document is already present in the index
    #
    # Signature of the function:
    #  Input:
    #       esIndex: ElasticSearch or OpenSearch connection
    #       indexName: Name of the index that needs to be created
    #       celexList: List of the celex number for which the summary and content needs to be extracted
    #
    #  Output:
    #       nonExisting: List of all the celex number that are not present in the ElasticSearch or OpenSearch index
    # """"""""""
    # Convert the list of IDs to a list of dicts with "_id" keys
    id_list = [{"_id": id} for id in id_list]
    non_existing = []

    if len(id_list) != 0:

        # Make the multi-get request to OpenSearch
        response = os_index.mget(index=index_name, body={"docs": id_list})

        # Extract the IDs that were not found in OpenSearch
        non_existing = [doc["_id"] for doc in response["docs"] if not doc["found"]]

    return non_existing
