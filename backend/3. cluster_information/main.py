import logging
from tasks import *
import joblib
import numpy as np
import os
from utils import load_config_from_env
import argparse
import pickle
from sklearn.utils import shuffle
from umap import UMAP

CONFIG = load_config_from_env()

# TODO: Add timing during processing of each step


def main():
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

        logging.info("Starting the clustering and indexing pipeline.")

        os_connection = opensearch_connection()

        # Initialize DataFetcher
        os_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_COMPLETE"]
        cluster_index_name = CONFIG["CLUSTER_CHAT_CLUSTER_INFORMATION_INDEX"]
        document_index_name = CONFIG["CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX"]
        model_path = CONFIG["MODEL_PATH"]

        # parse command line arguments
        parser = argparse.ArgumentParser(description="Clustering Pipeline")
        parser.add_argument(
            "-c",
            "--clusterinformation",
            metavar=("START_DATE", "END_DATE"),
            type=str,
            nargs=2,
            help=(
                "Storing cluster information "
                "based on date range in YYYY-MM-DD format."
            ),
        )

        args = parser.parse_args()

        if args.clusterinformation:
            start_date, end_date = args.clusterinformation

            data_fetcher = DataFetcher(
                opensearch_connection=os_connection,
                index_name=os_index,
                start_date=start_date,
                end_date=end_date,
            )

            # Step 2: Process BERTopic models
            merged_topics_path = os.path.join(model_path, "merged_topics.pkl")
            topic_label_path = os.path.join(model_path, "topic_label.pkl")
            topic_description_path = os.path.join(model_path, "topic_description.pkl")
            topic_words_path = os.path.join(model_path, "topic_words.pkl")
            merged_embeddings_path = os.path.join(
                model_path, "merged_topic_embeddings_array.npy"
            )

            if all(
                os.path.exists(path)
                for path in [
                    merged_topics_path,
                    topic_label_path,
                    topic_description_path,
                    topic_words_path,
                    merged_embeddings_path,
                ]
            ):
                logging.info("Existing processed data found. Loading from files.")
                with open(merged_topics_path, "rb") as f:
                    merged_topics = pickle.load(f)
                with open(topic_label_path, "rb") as f:
                    topic_label = pickle.load(f)
                with open(topic_description_path, "rb") as f:
                    topic_description = pickle.load(f)
                with open(topic_words_path, "rb") as f:
                    topic_words = pickle.load(f)
                merged_topic_embeddings_array = np.load(merged_embeddings_path)
            else:
                (
                    merged_topics,
                    merged_topic_embeddings_array,
                    topic_label,
                    topic_description,
                    topic_words,
                ) = process_models(model_path)

            # Step 3: Load UMAP model
            logging.info(f"Loading the trained UMAP model")
            umap_path = os.path.join(model_path, "umap_2_components.joblib")

            if os.path.exists(umap_path):
                logging.info("Existing UMAP model found. Loading from files.")
                with open(umap_path, "rb") as f:
                    umap_model = joblib.load(f)
            else:
                embeddings = shuffle(merged_topic_embeddings_array, random_state=42)
                umap_model = UMAP(n_components=2, n_jobs=1, random_state=42)
                # Fit UMAP on topic embeddings only
                umap_model.fit(embeddings)
                joblib.dump(
                    umap_model, os.path.join(model_path, "umap_2_components.joblib")
                )

            logging.info(f"Loading the UMAP model completed")

            # Step 4: Build hierarchy
            clusters, cluster_embeddings = build_custom_hierarchy(
                merged_topic_embeddings_array,
                merged_topics,
                topic_label,
                topic_description,
                topic_words,
                umap_model,
                model_path,
            )

            # Step 5: Index clusters into OpenSearch
            create_cluster_index(os_connection, cluster_index_name)
            index_clusters(
                os_connection, cluster_index_name, clusters, cluster_embeddings
            )

            # Step 6: Update cluster paths in OpenSearch
            update_cluster_paths(os_connection, cluster_index_name)

            # Step 7: Index documents into OpenSearch
            create_document_index(os_connection, document_index_name)

            # Index documents
            index_documents(
                os_connection,
                document_index_name,
                data_fetcher,
                umap_model,
                merged_topic_embeddings_array,
            )

            logging.info("Clustering and indexing pipeline completed successfully.")

    finally:
        # Close OpenSearch connection
        os_connection.close()


if __name__ == "__main__":
    main()
