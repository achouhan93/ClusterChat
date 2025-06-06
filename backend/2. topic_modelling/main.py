import os
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from tqdm import tqdm

from tasks.database.database_connection import opensearch_connection
from tasks.database.database_read import DataFetcher
from tasks.topic_modelling import TopicModeller
from utils import load_config_from_env

# Load configuration
CONFIG = load_config_from_env()


def generate_date_ranges(
    start_date: datetime, end_date: datetime, delta_days: int = 15
) -> List[Tuple[str, str]]:
    """
    Generate a list of (start_date, end_date) string tuples over a given interval.

    Args:
        start_date (datetime): The beginning of the date range.
        end_date (datetime): The end of the date range.
        delta_days (int): Length of each date range in days. Defaults to 15.

    Returns:
        List[Tuple[str, str]]: List of (start_date, end_date) in 'YYYY-MM-DD' format.
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


def main(argv: Optional[List[str]] = None) -> None:
    """
    Entry point for the BERTopic clustering pipeline.

    Parses command-line arguments, connects to OpenSearch, fetches data,
    and trains/saves topic models on document batches.
    """
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

        # Path to save trained BERTopic models
        intermediate_path = CONFIG["MODEL_PATH"]
        os.makedirs(intermediate_path, exist_ok=True)

        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Run BERTopic Clustering Pipeline")

        parser.add_argument(
            "-c",
            "--clusterchatbackend",
            metavar=("START_DATE", "END_DATE"),
            type=str,
            nargs=2,
            help=(
                "Based on date range in YYYY-MM-DD format. "
                "Trains and stores BERTopic Model."
            ),
        )

        args = parser.parse_args()

        if args.clusterchatbackend:
            start_date, end_date = args.clusterchatbackend

            try:
                min_date = datetime.strptime(start_date, "%Y-%m-%d")
                max_date = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as ve:
                logging.error("Invalid date format. Please use 'YYYY-MM-DD'.")
                raise ve

            # Initialize components
            data_fetcher = DataFetcher(
                opensearch_connection=os_connection, index_name=os_index
            )
            topic_modelling = TopicModeller(model_path=intermediate_path)

            # Create date batches and process each batch
            date_batches = generate_date_ranges(min_date, max_date, delta_days=15)
            logging.info(f"Generated {len(date_batches)} date batches for processing.")

            for date_range in tqdm(date_batches, desc="Training models by date range"):
                logging.info(f"Training BERTopic model for range: {date_range}")
                topic_modelling.train_bertopic_model(
                    date_range=date_range, data_fetcher=data_fetcher
                )

            logging.info("Clustering pipeline execution completed.")

    except Exception as e:
        logging.error(f"Clustering pipeline encountered an error: {str(e)}")

    finally:
        # Close OpenSearch connection
        os_connection.close()


if __name__ == "__main__":
    main()
