import os
import sys
import spacy
import argparse
import logging
from time import time
from typing import Optional, List
from datetime import datetime, timedelta, date

from tqdm import tqdm
from torch import cuda
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import SentenceTransformersTokenTextSplitter

from tasks import *
from utils import load_config_from_env


# Constants
CONST_EUTILS_DEFAULT_MINDATE = "1800-01-01"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y-%m-%d")
CONFIG = load_config_from_env()


class Processor:
    """
    Handles document retrieval, chunking, embedding, and insertion into OpenSearch.
    """

    def __init__(
        self,
        opensearch_connection,
        source_index: str,
        target_index: str,
        chunking_strategy: str,
        *args: str,
    ):
        """
        Initializes the Processor with OpenSearch connections, indexes, and chunking settings.

        Args:
            os_conn: OpenSearch client instance.
            source_index (str): Name of the source OpenSearch index.
            target_index (str): Name of the target OpenSearch index.
            chunking_strategy (str): Chunking method: "complete" or "sentence".
            *args (str): Optional date range (start_date, end_date).
        """
        self.nlp = spacy.load("en_core_sci_sm")  # Load the SciSpacy model
        self.os_connection = opensearch_connection
        self.source_index = source_index
        self.target_index = target_index
        self.chunking_strategy = chunking_strategy

        # index creation with mapping
        target_index_mapping = opensearch_pubmedbert_mapping()
        opensearch_create(opensearch_connection, target_index, target_index_mapping)

        # Load embedding model
        self.device = f"cuda:{cuda.current_device()}" if cuda.is_available() else "cpu"
        embed_model_id = CONFIG["CLUSTER_CHAT_EMBEDDING_MODEL"]

        self.embed_model = SentenceTransformer(
            model_name_or_path=embed_model_id,
            trust_remote_code=True,
            device=self.device,
        )
        self.splitter = SentenceTransformersTokenTextSplitter(model_name=embed_model_id)

        # Date range configuration
        if args and len(args[0]) != 0:
            # Convert start and end dates to datetime objects
            self.start_date = datetime.strptime(args[0], "%Y-%m-%d")
            self.end_date = datetime.strptime(args[1], "%Y-%m-%d")
        else:
            self.start_date = datetime.strptime(
                CONST_EUTILS_DEFAULT_MINDATE, "%Y-%m-%d"
            )
            self.end_date = datetime.strptime(CONST_EUTILS_DEFAULT_MAXDATE, "%Y-%m-%d")

        self.current_date = self.end_date
        self.scroll_size = 500

    def process_articles_in_batches(self) -> None:
        """
        Main loop to retrieve documents from OpenSearch, chunk, embed, and re-index them.
        """
        fields_to_include = [
            "title",
            "abstract",
            "articleDate",
            "authors",
            "keywords.name",
            "journalInformation.journalTitle",
            "meshTerms.meshID",
            "meshTerms.name",
            "chemicals.name",
        ]

        while self.current_date >= self.start_date:
            minDate = date.strftime("%Y-%m-%d")
            maxDate = self.current_date.strftime("%Y-%m-%d")
            date = self.current_date - timedelta(days=0)

            search_params = {
                "sort": [{"articleDate": {"order": "desc"}}],
                "query": {
                    "bool": {
                        "must": [
                            {"range": {"articleDate": {"gte": minDate, "lte": maxDate}}}
                        ],
                        "must_not": [
                            {
                                "match_phrase": {
                                    "abstract": "no abstract available on pubmed"
                                }
                            },
                            {"match_phrase": {"abstract": "ABSTRACT TRUNCATED AT"}},
                        ],
                    }
                },
                "_source": fields_to_include,
            }

            # Execute the initial search request
            response = self.os_connection.search(
                index=self.source_index,
                scroll="10m",
                size=self.scroll_size,
                body=search_params,
            )

            # Get the scroll ID and hits from the initial search request
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]
            total_docs = response["hits"]["total"][
                "value"
            ]  # Get the total number of documents

            with tqdm(total=total_docs) as pbar:
                while hits:
                    try:
                        logging.info(f"Considered {len(hits)} documents for processing")
                        document_vector_information = self.get_document_information(
                            hits
                        )

                        if document_vector_information:
                            loadSuccess = opensearch_insert(
                                self.os_connection,
                                self.target_index,
                                document_vector_information,
                            )

                        if not loadSuccess:
                            logging.error(
                                f"\nOperation unsuccessful, see logs for more information."
                            )
                        else:
                            logging.info(
                                f"\nOperation successful for {len(hits)} documents."
                            )

                    except Exception as e:
                        logging.error(
                            f"Error during vector create and storage operation due to error {e}"
                        )

                    pbar.update(len(hits))

                    # Paginate through the search results using the scroll parameter
                    response = self.os_connection.scroll(
                        scroll_id=scroll_id, scroll="10m"
                    )
                    hits = response["hits"]["hits"]
                    scroll_id = response["_scroll_id"]

            # Clear the scroll
            self.os_connection.clear_scroll(scroll_id=scroll_id)
            pbar.close()
            self.current_date -= timedelta(days=1)
            logging.info(
                f"Processing for {total_docs} completed for the date {minDate}"
            )

        logging.info(
            f"Processing for all documents in the date range of {self.start_date} to {self.end_date} completed"
        )

    def get_document_information(self, documents: List[dict]) -> List[tuple]:
        """
        Parses, chunks, and encodes documents into vectors.

        Args:
            documents (List[dict]): List of documents returned by OpenSearch.

        Returns:
            List[tuple]: List of (id, vector, metadata) tuples for re-indexing.
        """
        vector_data = []

        for doc in tqdm(documents, desc="Chunking & encoding"):
            try:
                doc_id = doc["_id"]

                logging.info(f"Started data creation for pubmed id: {doc_id}")

                if doc["_source"]["journalInformation"] is not None:
                    doc["_source"]["journalInformation"]["journalTitle"] = (
                        "no journal information"
                        if doc["_source"]["journalInformation"]["journalTitle"] is None
                        else doc["_source"]["journalInformation"]["journalTitle"]
                    )
                else:
                    doc["_source"]["journalInformation"][
                        "journalTitle"
                    ] = "no journal information"

                if doc["_source"].get("keywords") is not None:
                    doc["_source"]["keywords"] = (
                        ["no keywords"]
                        if doc["_source"]["keywords"] is None
                        else list(
                            {
                                term["name"].lower()
                                for term in doc["_source"]["keywords"]
                            }
                        )
                    )
                else:
                    doc["_source"]["keywords"] = ["no keywords"]

                if doc["_source"].get("meshTerms") is not None:
                    doc["_source"]["meshNames"] = (
                        ["no mesh names"]
                        if doc["_source"]["meshTerms"] is None
                        else list(
                            {
                                term["name"].lower()
                                for term in doc["_source"]["meshTerms"]
                            }
                        )
                    )
                    doc["_source"]["meshIds"] = (
                        ["no mesh ids"]
                        if doc["_source"]["meshTerms"] is None
                        else list(
                            {term["meshID"] for term in doc["_source"]["meshTerms"]}
                        )
                    )
                else:
                    doc["_source"]["meshNames"] = ["no mesh names"]
                    doc["_source"]["meshIds"] = ["no mesh ids"]

                if doc["_source"].get("chemicals") is not None:
                    doc["_source"]["chemicals"] = (
                        ["no chemicals"]
                        if doc["_source"]["chemicals"] is None
                        else list(
                            {
                                term["name"].lower()
                                for term in doc["_source"]["chemicals"]
                            }
                        )
                    )
                else:
                    doc["_source"]["chemicals"] = ["no chemicals"]

                if doc["_source"].get("authors") is not None:
                    doc["_source"]["authorNames"] = (
                        ["no author names"]
                        if doc["_source"]["authors"] is None
                        else list(
                            {
                                f"{author['firstName']} {author['lastName']}"
                                for author in doc["_source"]["authors"]
                            }
                        )
                    )
                    doc["_source"]["authorAffiliations"] = list(
                        {
                            (
                                affiliation["institute"]
                                if affiliation
                                else "no affiliation"
                            )
                            for author in doc["_source"]["authors"]
                            for affiliation in author["affiliations"]
                        }
                    )
                else:
                    doc["_source"]["authorNames"] = ["no author names"]
                    doc["_source"]["authorAffiliations"] = ["no affiliation"]

                # Text Chunking
                if self.chunking_strategy == "complete":
                    # Chunks created based on the transformer
                    chunks = self.splitter.split_text(text=doc["_source"]["abstract"])

                elif self.chunking_strategy == "sentence":
                    abstract_text = doc["_source"]["abstract"]
                    doc_spacy = self.nlp(
                        abstract_text
                    )  # Process the text with SciSpacy
                    chunks = [
                        sent.text.strip() for sent in doc_spacy.sents
                    ]  # Extract sentences

                # Embedding
                for j, chunk in enumerate(chunks):
                    # Add metadata for article ID and chunk ID
                    metadata = {
                        "pubmed_id": doc_id,
                        "articleDate": doc["_source"]["articleDate"],
                        "title": (
                            "no title"
                            if doc["_source"]["title"] is None
                            else doc["_source"]["title"]
                        ),
                        "journalTitle": doc["_source"]["journalInformation"][
                            "journalTitle"
                        ],
                        "keywords": doc["_source"]["keywords"],
                        "meshTerms": doc["_source"]["meshNames"],
                        "meshIds": doc["_source"]["meshIds"],
                        "chemicals": doc["_source"]["chemicals"],
                        "authorNames": doc["_source"]["authorNames"],
                        "authorAffiliations": doc["_source"]["authorAffiliations"],
                        "text_chunk_id": j,
                        "pubmed_text": chunk,
                        "document_source": self.source_index,
                    }

                    #  Embed the chunk using huggingface embedding method
                    embedding = self.embed_model.encode(chunk).tolist()
                    ids = f"{doc_id}_{j}"
                    vector_data.append((ids, embedding, metadata))

                logging.info(f"Completed data creation for pubmed id: {doc_id}")

            except Exception as e:
                logging.exception(f"Error processing document ID {doc_id}: {str(e)}")

        return vector_data


def seconds_to_text(secs: float) -> str:
    """
    Converts seconds to a human-readable string format.

    Args:
        secs (float): Time in seconds.

    Returns:
        str: Readable duration string.
    """
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes * 60
    result = (
        ("{0} day{1}, ".format(days, "s" if days != 1 else "") if days else "")
        + ("{0} hour{1}, ".format(hours, "s" if hours != 1 else "") if hours else "")
        + (
            "{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "")
            if minutes
            else ""
        )
        + (
            "{0} second{1}, ".format(round(seconds, 2), "s" if seconds != 1 else "")
            if seconds
            else ""
        )
    )
    return result


def main(argv: Optional[List[str]] = None) -> None:
    try:
        CONFIG = load_config_from_env()

        if not os.path.exists(CONFIG["CLUSTER_CHAT_LOG_PATH"]):
            os.makedirs(CONFIG["CLUSTER_CHAT_LOG_PATH"])

        logging.basicConfig(
            filename=CONFIG["CLUSTER_CHAT_LOG_EXE_PATH"],
            filemode="a",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%m-%y %H:%M:%S",
            level=logging.INFO,
        )

        os_connection = opensearch_connection()
        source_os_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]

        # parse command line arguments
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-v",
            "--vectorcreation",
            metavar="date-range",
            type=str,
            nargs="*",
            default=[],
            help="Storing the vector embeddings in Opensearch based on date range in yyyy-mm-dd",
        )

        parser.add_argument(
            "-c",
            "--chunking",
            type=str,
            choices=["complete", "sentence"],
            default="complete",
            help="Chunking strategy for text processing.",
        )

        args = parser.parse_args()

        if args.chunking == "complete":
            target_os_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_COMPLETE"]
        elif args.chunking == "sentence":
            target_os_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_SENTENCE"]

        if len(args.vectorcreation) >= 0:
            if len(args.vectorcreation) == 1:
                print("--range expects two arguments: <mindate, maxdate>")
                sys.exit()
            elif len(args.vectorcreation) == 2:
                document_processor = Processor(
                    os_connection,
                    source_os_index,
                    target_os_index,
                    args.chunking,
                    args.vectorcreation[0],
                    args.vectorcreation[1],
                )
                start_time = time()
                logging.info(
                    f"Vector storage for pubmed records started at {seconds_to_text(start_time)}"
                )
                document_processor.process_articles_in_batches()
                logging.info(
                    f"Vector storage for pubmed records completed at {seconds_to_text(time()- start_time)}"
                )
            elif len(args.vectorcreation) == 0:
                res = ""
                while res != "n":
                    res = input(
                        "Are you sure you want to insert all records starting from start date till date? This can take several days. (y/n): "
                    )
                    if res == "y":
                        start_time = time()
                        document_processor = Processor(
                            os_connection,
                            source_os_index,
                            target_os_index,
                            args.chunking,
                            args.vectorcreation,
                        )
                        logging.info(
                            f"Vector storage for pubmed records started at {seconds_to_text(start_time)}"
                        )
                        document_processor.process_articles_in_batches()
                        logging.info(
                            f"Vector storage for pubmed records completed at {seconds_to_text(time()- start_time)}"
                        )
                        res = "n"
            else:
                print("--vectorcreation expects two arguments: <mindate, maxdate>")
                sys.exit()

    finally:
        os_connection.close()
        logging.info("OpenSearch connection closed.")


if __name__ == "__main__":
    main()
