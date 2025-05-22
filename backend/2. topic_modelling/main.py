from tasks.database.database_connection import opensearch_connection
from tasks.database.database_read import DataFetcher
from tasks.topic_modelling import TopicModeller
from utils import load_config_from_env

from datetime import datetime, timedelta, date
import logging
import argparse
from tqdm import tqdm
import os

CONFIG = load_config_from_env()


def generate_date_ranges(start_date, end_date, delta_days=15):
    """
    Generate a list of date ranges between start_date and end_date, each with delta_days.

    Args:
        start_date (datetime): The start date.
        end_date (datetime): The end date.
        delta_days (int): Number of days in each range.

    Returns:
        list of tuples: List of (start_date, end_date) tuples.
    """
    date_ranges = []
    current_start = start_date
    while current_start <= end_date:
        current_end = min(current_start + timedelta(days=delta_days - 1), end_date)
        date_ranges.append(
            (current_start.strftime("%Y-%m-%d"), current_end.strftime("%Y-%m-%d"))
        )
        current_start = current_end + timedelta(days=1)
    return date_ranges


def main(argv=None):
    """Main function to run the clustering pipeline."""
    try:
        if not os.path.exists(CONFIG["CLUSTER_CHAT_LOG_PATH"]):
            os.makedirs(CONFIG["CLUSTER_CHAT_LOG_PATH"])

        logging.basicConfig(
            filename=CONFIG["CLUSTER_CHAT_LOG_EXE_PATH"],
            filemode="a",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%m-%y %H:%M:%S",
            level=logging.INFO,
        )

        # Establish OpenSearch Connection
        os_connection = opensearch_connection()
        os_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_COMPLETE"]
        intermediate_path = CONFIG["MODEL_PATH"]
        os.makedirs(intermediate_path, exist_ok=True)

        # parse command line arguments
        parser = argparse.ArgumentParser(description="Clustering Pipeline")
        parser.add_argument(
            "-c",
            "--clusterchatbackend",
            metavar=("START_DATE", "END_DATE"),
            type=str,
            nargs=2,
            help=(
                "Based on date range in YYYY-MM-DD format, "
                "train and store the BERTopic Model."
            ),
        )

        args = parser.parse_args()

        if args.clusterchatbackend:
            start_date, end_date = args.clusterchatbackend
            min_date = datetime.strptime(start_date, "%Y-%m-%d")
            max_date = datetime.strptime(end_date, "%Y-%m-%d")

            # Initialize components
            data_fetcher = DataFetcher(
                opensearch_connection=os_connection, index_name=os_index
            )

            # Generate date ranges for batching (every 15 days)
            date_batches = generate_date_ranges(min_date, max_date, delta_days=15)
            topic_modelling = TopicModeller(model_path=intermediate_path)

            for date_range in tqdm(date_batches):
                topic_modelling.train_bertopic_model(
                    date_range=date_range, data_fetcher=data_fetcher
                )

    finally:
        # Close OpenSearch connection
        os_connection.close()


if __name__ == "__main__":
    main()
