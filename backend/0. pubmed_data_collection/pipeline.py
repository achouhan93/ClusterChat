import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, date
from time import time
from typing import Optional, List

from tqdm import tqdm

import utils
from pipeline_components.extractor import (
    extract_articles_data,
    get_article_ids_for_time_range,
)
from pipeline_components.transformer import transform_articles
from pipeline_components.loader import load_articles
from pipeline_helpers.loader_helper.database_main import opensearch_connection

# Logger configuration
log = logging.getLogger(__name__)

# Constants
CONST_EUTILS_DEFAULT_MINDATE = "1900"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y/%m/%d")


def insert_articles_by_time_range(
    database_connection: object,
    index_name: List[str],
    *args: str,
    batch_size: int = 100,
) -> None:
    """
    Inserts articles in a given date range into the OpenSearch index in batches.

    Args:
        database_connection (object): Connection to the OpenSearch instance.
        index_name (List[str]): Name of the OpenSearch index to populate.
        *args (str): Optional. Two strings specifying start and end dates (format: yyyy/mm/dd).
        batch_size (int, optional): Number of articles per batch insert. Defaults to 100.

    Returns:
        None
    """
    if args:
        # Convert start and end dates to datetime objects
        start_date = datetime.strptime(args[0], "%Y/%m/%d")
        end_date = datetime.strptime(args[1], "%Y/%m/%d")
    else:
        start_date = datetime.strptime(CONST_EUTILS_DEFAULT_MINDATE, "%Y")
        end_date = datetime.strptime(CONST_EUTILS_DEFAULT_MAXDATE, "%Y/%m/%d")

    # Loop over the range of dates between start and end dates, with two days apart
    current_date = end_date

    while current_date >= start_date:
        max_date_str = current_date.strftime("%Y/%m/%d")
        min_date_str = (current_date - timedelta(days=0)).strftime("%Y/%m/%d")

        article_ids = get_article_ids_for_time_range(
            "pubmed", min_date_str, max_date_str, index_name
        )
        log.info(f"Retrieved {len(article_ids)} article IDs for date: {min_date_str}")

        failed = False

        for id_batch in tqdm(
            [
                article_ids[i : i + batch_size]
                for i in range(0, len(article_ids), batch_size)
            ],
            desc=f"Inserting article batches (size={batch_size})",
        ):
            id_str = ",".join(map(str, id_batch))
            articles = extract_articles_data("pubmed", id_str)
            transformed_articles = transform_articles(articles)
            success = load_articles(
                database_connection, transformed_articles, index_name
            )

            if not success:
                log.error("Batch insert failed for date: %s", min_date_str)
                failed = True
                print("\nOperation unsuccessful. Check logs for details.")

        if not failed:
            print(
                f"\nOperation successful. Inserted/updated {len(article_ids)} articles."
            )
            current_date -= timedelta(days=1)


def main(argv: Optional[List[str]] = None) -> None:
    """
    Main entry point of the pipeline execution script.

    Args:
        argv (Optional[List[str]]): Command-line arguments. Defaults to None.

    Returns:
        None
    """
    config = utils.load_config_from_env()
    log_dir = config.get("CLUSTER_CHAT_LOG_PATH")
    log_file = config.get("CLUSTER_CHAT_LOG_EXE_PATH")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created directory: {log_dir}")

    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
    )

    start_time = time()
    logging.info("Current date and time: " + str(start_time))

    index_name = [config["CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX"]]
    database_connection = opensearch_connection(index_name)

    parser = argparse.ArgumentParser("Specify which articles you want to fetch")

    parser.add_argument(
        "--range",
        metavar="date-range",
        type=str,
        nargs="*",
        help="Start date of range in yyyy/mm/dd and End date of range in yyyy/mm/dd",
    )

    args = parser.parse_args()

    if args.range:
        if len(args.range) == 1 or len(args.range) > 2:
            print("--range expects two arguments: <mindate, maxdate>")
            sys.exit()
        elif len(args.range) == 0:
            res = ""
            while res != "n":
                res = input(
                    "Are you sure you want to insert the records starting from 1900 till date? This can take several days. (y/n)"
                )
                if res == "y":
                    insert_articles_by_time_range(
                        database_connection, index_name, args.range
                    )
                    res = "n"
        elif len(args.range) == 2:
            insert_articles_by_time_range(
                database_connection, index_name, args.range[0], args.range[1]
            )

        log.info("Pipeline completed.")
        print("Pipeline execution completed.")

    else:
        print("provide at least one argument.")
        sys.exit()


if __name__ == "__main__":
    main()
