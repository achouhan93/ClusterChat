"""
Main script to orchestrate the clustering pipeline.

This script performs the following steps:
1. Fetch embeddings from OpenSearch within a specified date range.
2. Perform dimensionality reduction using UMAP or IncrementalPCA.
3. Cluster the reduced embeddings using HDBSCAN or BIRCH.
4. Reduce the embeddings to 2D for visualization.
5. Store the final results and intermediate models.

Usage:
    python main.py -c <start_date> <end_date>
"""
import os
import argparse
import logging

from tasks.database.database_connection import opensearch_connection
from tasks.database.database_read import DataFetcher
from tasks.database.database_storage import StorageManager
from tasks.dimensionality_reduction import DimensionalityReducer
from tasks.clustering import ClusteringModel
from utils import log_time_memory, load_config_from_env
import config

# Load configuration
CONFIG = load_config_from_env()

def main(argv=None):
    """Main function to run the clustering pipeline."""
    try:
        # Ensure log directory exists
        if not os.path.exists(CONFIG["CLUSTER_TALK_LOG_PATH"]):
            os.makedirs(CONFIG["CLUSTER_TALK_LOG_PATH"])

        # Configure logging
        logging.basicConfig(
            filename=CONFIG["CLUSTER_TALK_LOG_EXE_PATH"],
            filemode="a",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d-%m-%y %H:%M:%S",
            level=logging.INFO,
        )

        # Establish OpenSearch Connection
        os_connection = opensearch_connection()
        os_index = CONFIG["CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_COMPLETE"]

        # Parse command-line arguments
        parser = argparse.ArgumentParser(description="Clustering Pipeline")
        parser.add_argument(
            "-c",
            "--clustering",
            metavar=("START_DATE","END_DATE"),
            type=str,
            nargs=2,
            help=(
                "Perform clustering and store the final cluster information "
                "based on date range in YYYY-MM-DD format."
            ),
        )

        args = parser.parse_args()

        if args.clustering:
            start_date, end_date = args.clustering

            # Initialize components
            data_fetcher = DataFetcher(
                opensearch_connection=os_connection,
                index_name=os_index,
                start_date=start_date,
                end_date=end_date,
            )

            storage_manager = StorageManager(opensearch_connection=os_connection)
            reducer = DimensionalityReducer(
                method=config.DIMENSIONALITY_REDUCTION_METHOD
            )
            clusterer = ClusteringModel(method=config.CLUSTERING_METHOD)

            # Step 1: Dimensionality Reduction
            logging.info(
                f"Starting dimensionality reduction using "
                f"{config.DIMENSIONALITY_REDUCTION_METHOD} method."
            )
            reducer.fit(data_fetcher.fetch_embeddings)

            # Save the fitted reducer
            storage_manager.save_intermediate('reducer.joblib', reducer.reducer)
            
            logging.info(
                f"Finished dimensionality reduction using "
                f"{config.DIMENSIONALITY_REDUCTION_METHOD} method "
                f"and stored in reducer.joblib."
            )

            # Step 2: Clustering
            logging.info(
                f"Starting clustering using {config.CLUSTERING_METHOD} algorithm."
            )

            @log_time_memory
            def data_generator():
                """Generator function to yield reduced embeddings and IDs."""
                for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings():
                    reduced_embeddings = reducer.transform(embeddings_batch)
                    yield reduced_embeddings, ids_batch

            clusterer.fit(data_generator)
            storage_manager.save_intermediate("clusterer.joblib", clusterer.model)

            logging.info(
                f"Finished clustering using {config.CLUSTERING_METHOD} algorithm "
                f"and stored in clusterer.joblib."
            )

            # Step 2.1: Store Cluster Information
            logging.info("Storing cluster information.")
            cluster_info = clusterer.get_cluster_info()
            storage_manager.store_cluster_info(cluster_info)
            logging.info("Cluster information stored successfully.")

            # Step 3: Reduction to 2D and storing results
            logging.info("Reducing embeddings to 2D for visualization.")

            for embeddings_batch, ids_batch in data_fetcher.fetch_embeddings():
                reduced_embeddings = reducer.transform(embeddings_batch)
                labels = clusterer.predict(reduced_embeddings)

                # Reduce to 2D using UMAP
                reducer_2d = DimensionalityReducer(method="UMAP", n_components=2)
                embeddings_2d = reducer_2d.fit_transform(reduced_embeddings)

                # Store results
                storage_manager.store_results(embeddings_2d, ids_batch, labels)

            logging.info("Clustering pipeline completed successfully.")
    
    finally:
        # Close OpenSearch connection
        os_connection.close()

if __name__ == '__main__':
    main()