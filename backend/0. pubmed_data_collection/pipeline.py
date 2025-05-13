from tqdm import tqdm
from datetime import datetime, timedelta, date
import sys
import argparse
import logging
import os
import utils
from time import time

from pipeline_components.extractor import (
    extractArticlesData,
    getArticleIdsForTimeRange,
)
from pipeline_components.transformer import transformArticles
from pipeline_components.loader import loadArticles
from pipeline_helpers.loader_helper.database_main import opensearch_connection


log = logging.getLogger(__name__)

CONST_EUTILS_DEFAULT_MINDATE = "1900"
CONST_EUTILS_DEFAULT_MAXDATE = date.today().strftime("%Y/%m/%d")


def insertArticlesByTimeRange(database, index_name, *args, batchSize=100):

    if args:
        # Convert start and end dates to datetime objects
        start_date = datetime.strptime(args[0], "%Y/%m/%d")
        end_date = datetime.strptime(args[1], "%Y/%m/%d")
    else:
        start_date = CONST_EUTILS_DEFAULT_MINDATE
        end_date = CONST_EUTILS_DEFAULT_MAXDATE

    # Loop over the range of dates between start and end dates, with two days apart
    current_date = end_date

    while current_date >= start_date:
        maxdate = current_date.strftime("%Y/%m/%d")
        date = current_date - timedelta(days=0)
        mindate = date.strftime("%Y/%m/%d")

        allIds = getArticleIdsForTimeRange("pubmed", mindate, maxdate, database)
        log.info(f"Considered {len(allIds)} new articles for Date: {mindate}")

        failed = False

        for idBatch in tqdm(
            [allIds[i : i + batchSize] for i in range(0, len(allIds), batchSize)],
            desc=f"Inserting all new article batches(size={batchSize})",
        ):
            allIdsString = ",".join([str(id) for id in idBatch])
            articleList = extractArticlesData("pubmed", allIdsString)
            transformed_articles = transformArticles(articleList)
            loadSuccess = loadArticles(database, transformed_articles, index_name)
            if not loadSuccess:
                print(f"\nOperation unsuccessful, see logs for more information.")
                failed = True
        if not failed:
            print(f"\nOperation successful, inserted/updated {len(allIds)} articles.")
            current_date -= timedelta(days=1)


def main(argv=None):
    CONFIG = utils.load_config_from_env()

    if not os.path.exists(CONFIG["CLUSTER_TALK_LOG_PATH"]):
        os.makedirs(CONFIG["CLUSTER_TALK_LOG_PATH"])
        print(f'created: {CONFIG["CLUSTER_TALK_LOG_PATH"]} directory.')

    logging.basicConfig(
        filename=CONFIG["CLUSTER_TALK_LOG_EXE_PATH"],
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
    )

    start_time = time()
    logging.info("Current date and time: " + str(start_time))

    database = [CONFIG["CLUSTER_TALK_OPENSEARCH_SOURCE_INDEX"]]
    database_connection = opensearch_connection(database)

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
        if len(args.range) == 1:
            print("--range expects two arguments: <mindate, maxdate>")
            sys.exit()
        elif len(args.range) == 0:
            res = ""
            while res != "n":
                res = input(
                    "Are you sure you want to insert the records starting from 1900 till date? This can take several days. (y/n)"
                )
                if res == "y":
                    insertArticlesByTimeRange(database_connection, database, args.range)
                    res = "n"
        elif len(args.range) == 2:
            insertArticlesByTimeRange(
                database_connection, database, args.range[0], args.range[1]
            )
        else:
            print("--range expects two arguments: <mindate, maxdate>")
            sys.exit()

    else:
        print("provide at least one argument.")
        sys.exit()


if __name__ == "__main__":
    main()
