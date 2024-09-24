from tqdm import tqdm
import logging


def opensearch_insert(os_connection, index_name, document_details, batch_size=1000):
    # """"""""""
    # Functionality: Insert the document in OpenSearch Index
    #
    # Signature of the function:
    #  Input:
    #       os_connection: OpenSearch connection
    #       index_name: Name of the index that needs to be created
    #       document_details: Information that needs to be inserted in the Index in JSON format
    #
    #  Output:
    #       Insert the information in the ElasticSearch or OpenSearch Index keeping unqiue ID (_id) as the pubmed chunk ID
    # """"""""""
    success = True
    total_docs = len(document_details)

    # Split the document details into batches of size `batch_size`
    for start in tqdm(
        range(0, total_docs, batch_size), desc="Saving document in database"
    ):
        actions = []
        batch = document_details[start : start + batch_size]

        for document_information in tqdm(batch):
            action = {"index": {"_index": index_name, "_id": document_information[0]}}
            doc = {
                "documentSource": document_information[2]["document_source"],
                "documentID": document_information[2]["pubmed_id"],
                "articleDate": document_information[2]["articleDate"],
                "title": document_information[2]["title"],
                "journal:title": document_information[2]["journalTitle"],
                "keywords:name": document_information[2]["keywords"],
                "meshTerms": document_information[2]["meshTerms"],
                "meshIds": document_information[2]["meshIds"],
                "chemicals": document_information[2]["chemicals"],
                "authors:name": document_information[2]["authorNames"],
                "authors:affiliation": document_information[2]["authorAffiliations"],
                "abstract_chunk_id": document_information[2]["text_chunk_id"],
                "abstract_chunk": document_information[2]["pubmed_text"],
                "pubmed_bert_vector": document_information[1],
            }
            actions.append(action)
            actions.append(doc)
        try:
            os_connection.bulk(index=index_name, body=actions)
        except Exception as e:
            logging.error(
                f"Bulk Indexing failed for batch {start//batch_size+1} due to error: {e}"
            )
            success = False

    return success
