import os
import gc
import json
import pickle
import logging
from time import sleep
from typing import List, Tuple, Dict, Any, Optional, Union

import numpy as np
from bertopic import BERTopic
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

from utils import load_config_from_env

# Configure logging
logger = logging.getLogger(__name__)

# Load environment configuration and initialize OpenAI client
CONFIG: Dict[str, str] = load_config_from_env()
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def list_bertopic_models(model_path: str) -> List[str]:
    """
    List all BERTopic model files in the given directory.

    Args:
        model_path (str): Path to the directory containing BERTopic models.

    Returns:
        List[str]: List of file paths to BERTopic model pickle files.
    """
    model_files: List[str] = []
    for root, _, files in os.walk(model_path):
        for file in files:
            if file.startswith("bertopic_model_") and file.endswith(".pkl"):
                model_files.append(os.path.join(root, file))
    return model_files


def get_topic_metadata(
    topic_words: List[Tuple[str, float]]
) -> Dict[str, Optional[str]]:
    """
    Generate structured metadata (label and description) for a topic using OpenAI.

    Args:
        topic_words (List[Tuple[str, float]]): Topic words with relevance scores.

    Returns:
        Dict[str, Optional[str]]: Dictionary with 'label' and 'description' or fallback values on error.
    """
    prompt = (
        f"You are given topic keywords in order of importance: {', '.join([word for word, _ in topic_words])}. "
        f"Generate a JSON object with the following two fields:\n"
        f"- 'label': A concise topic label using **at most three words**, summarizing the topic clearly. Do not use punctuation.\n"
        f"- 'description': A short informative sentence of **at most 15 words** that summarizes the topic, emphasizing the most important terms.\n\n"
        f"Return only a valid JSON object and nothing else."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that returns structured JSON data for topic modeling.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=50,
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        logger.warning("OpenAI response parsing failed: %s", e)
        return {
            "label": None,
            "description": None,
            "error": f"Failed to parse JSON: {e}",
            "raw_output": content if "content" in locals() else None,
        }


def save_checkpoint(checkpoint_path: str, checkpoint_data: Dict[str, Any]) -> None:
    """
    Persist checkpoint data to disk.

    Args:
        checkpoint_path (str): Destination file path.
        checkpoint_data (Dict[str, Any]): Serializable checkpoint data.
    """
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_data, f)
    logger.info(f"Checkpoint saved at {checkpoint_path}.")


def load_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    """
    Load checkpoint data from disk.

    Args:
        checkpoint_path (str): File path to load checkpoint from.

    Returns:
        Dict[str, Any]: Deserialized checkpoint data.
    """
    with open(checkpoint_path, "rb") as f:
        checkpoint_data = pickle.load(f)
    logger.info(f"Checkpoint loaded from {checkpoint_path}.")
    return checkpoint_data


def process_models(
    model_path: str,
) -> Tuple[
    Dict[str, List[Tuple[str, float]]],
    np.ndarray,
    Dict[str, str],
    Dict[str, str],
    Dict[str, List[str]],
]:
    """
    Process and merge multiple BERTopic models from a given path.

    Args:
        model_path (str): Directory containing BERTopic model files.

    Returns:
        Tuple containing:
            - merged_topics (Dict[str, List[Tuple[str, float]]])
            - merged_topic_embeddings_array (np.ndarray)
            - topic_label (Dict[str, str])
            - topic_description (Dict[str, str])
            - topic_words (Dict[str, List[str]])
    """
    checkpoint_path = os.path.join(model_path, "checkpoint.pkl")
    logger.info("Starting the processing of the BERTopic Model")

    # Initialize or load checkpoint
    if os.path.exists(checkpoint_path):
        checkpoint = load_checkpoint(checkpoint_path)
        merged_topics = checkpoint["merged_topics"]
        merged_topic_embeddings = checkpoint["merged_topic_embeddings"]
        topic_id_to_index = checkpoint["topic_id_to_index"]
        current_topic_id = checkpoint["current_topic_id"]
        topic_label = checkpoint["topic_label"]
        topic_description = checkpoint["topic_description"]
        topic_words = checkpoint["topic_words"]
        processed_models = checkpoint["processed_models"]
    else:
        # Initialize variables
        merged_topics = {}
        merged_topic_embeddings = []
        topic_id_to_index = {}
        current_topic_id = 0
        topic_label = {}
        topic_description = {}
        topic_words = {}
        processed_models = []

    # List all BERTopic models
    model_paths = list_bertopic_models(model_path)
    models_to_process = [m for m in model_paths if m not in processed_models]

    logger.info(
        f"Found {len(model_paths)} total models in path {model_path}. "
        "{len(models_to_process)} model(s) to process"
    )

    # Process models one at a time to minimize memory usage
    for model_num, path in enumerate(models_to_process, start=1):
        try:
            logger.info(
                f"Processing Started for model {model_num + 1}/{len(model_paths)}: {path}"
            )

            # Load the model
            model = BERTopic.load(path)

            # Extract topics and embeddings from the model
            topics = model.get_topics()
            embeddings = model.topic_embeddings_
            topic_keys = list(topics.keys())

            batch_topics = {}
            batch_topic_embeddings = []
            batch_topic_id_to_index = {}

            for i, topic_id in enumerate(topic_keys):
                if topic_id == -1:
                    continue  # Skip outlier topic
                # Assign a new topic ID
                new_topic_id = current_topic_id
                current_topic_id += 1
                batch_topics[new_topic_id] = topics[topic_id]
                batch_topic_id_to_index[new_topic_id] = len(batch_topic_embeddings)
                batch_topic_embeddings.append(embeddings[i])

            # Combine existing merged topics with batch topics
            all_topics = {**merged_topics, **batch_topics}
            all_topic_embeddings = merged_topic_embeddings + batch_topic_embeddings
            all_topic_id_to_index = {**topic_id_to_index, **batch_topic_id_to_index}

            # Free memory from the loaded model
            del model
            gc.collect()
            sleep(2)

            # Update the merged topics and embeddings for the next iteration
            merged_topics = all_topics
            merged_topic_embeddings = all_topic_embeddings
            topic_id_to_index = all_topic_id_to_index

            # Generate topic descriptions for new topics
            for tid in batch_topics.keys():
                words = batch_topics[tid]
                topic_words[tid] = [word for word, _ in words]
                metadata = get_topic_metadata(words)
                topic_label[tid] = metadata.get("label")
                topic_description[tid] = metadata.get("description")
                sleep(2)

            # Clean up variables to free memory
            del batch_topics
            del batch_topic_embeddings
            del batch_topic_id_to_index
            gc.collect()
            sleep(2)

            # Update processed models
            processed_models.append(path)

            # Save checkpoint after processing each model
            checkpoint_data = {
                "merged_topics": merged_topics,
                "merged_topic_embeddings": merged_topic_embeddings,
                "topic_id_to_index": topic_id_to_index,
                "current_topic_id": current_topic_id,
                "topic_label": topic_label,
                "topic_description": topic_description,
                "topic_words": topic_words,
                "processed_models": processed_models,
            }

            save_checkpoint(checkpoint_path, checkpoint_data)

            logger.info(
                f"Processing Completed for model {model_num + 1}/{len(model_paths)}: {path}"
            )
        except Exception as e:
            logger.error(f"Error processing model {path}: {e}")
            logger.error("Saving checkpoint before exiting.")
            # Save the current state before exiting
            checkpoint_data = {
                "merged_topics": merged_topics,
                "merged_topic_embeddings": merged_topic_embeddings,
                "topic_id_to_index": topic_id_to_index,
                "current_topic_id": current_topic_id,
                "topic_label": topic_label,
                "topic_description": topic_description,
                "topic_words": topic_words,
                "processed_models": processed_models,
            }
            save_checkpoint(checkpoint_path, checkpoint_data)
            logger.info("Exiting the script due to errors.")
            raise  # Re-raise the exception after saving checkpoint

    logger.info(
        "Processing for all models completed and topics are merged with topic information"
    )

    # Save the final merged_topic_embeddings_array
    merged_topic_embeddings_array = np.array(merged_topic_embeddings, dtype=np.float32)
    final_npy_path = os.path.join(model_path, "merged_topic_embeddings_array.npy")
    np.save(final_npy_path, merged_topic_embeddings_array)
    logger.info(f"Final merged_topic_embeddings_array.npy saved at {final_npy_path}.")

    # Optionally, save other merged data for future use
    with open(os.path.join(model_path, "merged_topics.pkl"), "wb") as f:
        pickle.dump(merged_topics, f)
    with open(os.path.join(model_path, "topic_label.pkl"), "wb") as f:
        pickle.dump(topic_label, f)
    with open(os.path.join(model_path, "topic_description.pkl"), "wb") as f:
        pickle.dump(topic_description, f)
    with open(os.path.join(model_path, "topic_words.pkl"), "wb") as f:
        pickle.dump(topic_words, f)

    logger.info("All merged topic information saved as pickle files.")

    # Optionally, remove the checkpoint file as processing is complete
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        logger.info(
            f"Checkpoint file {checkpoint_path} removed after successful processing."
        )

    return (
        merged_topics,
        merged_topic_embeddings_array,
        topic_label,
        topic_description,
        topic_words,
    )


def deduplicate_topics(
    merged_topics: Dict[str, List[Tuple[str, float]]],
    topic_label: Dict[str, str],
    topic_description: Dict[str, str],
    topic_words: Dict[str, List[str]],
    merged_topic_embeddings_array: np.ndarray,
    model_path: str,
    label_threshold: float = 0.9,
    embedding_similarity_threshold: float = 0.9,
) -> Tuple[
    Dict[str, List[Tuple[str, float]]],
    np.ndarray,
    Dict[str, str],
    Dict[str, str],
    Dict[str, List[str]],
]:
    """
    Deduplicate topics using fuzzy label matching and embedding similarity.

    Args:
        merged_topics (Dict[str, List[Tuple[str, float]]]): Merged topics dictionary.
        topic_label (Dict[str, str]): Topic labels.
        topic_description (Dict[str, str]): Topic descriptions.
        topic_words (Dict[str, List[str]]): Topic keywords.
        merged_topic_embeddings_array (np.ndarray): Topic embedding vectors.
        model_path (str): Directory path to store checkpoint and outputs.
        label_threshold (float): Minimum fuzzy label similarity ratio to consider for merging.
        embedding_similarity_threshold (float): Minimum cosine similarity for merging.

    Returns:
        Tuple: Deduplicated versions of all inputs.
    """
    checkpoint_path = os.path.join(model_path, "dedup_checkpoint.pkl")
    logger.info("Starting the topic deduplication process")

    if os.path.exists(checkpoint_path):
        checkpoint = load_checkpoint(checkpoint_path)
        return (
            checkpoint["cleaned_merged_topics"],
            checkpoint["cleaned_merged_topic_embeddings"],
            checkpoint["cleaned_topic_label"],
            checkpoint["cleaned_topic_description"],
            checkpoint["cleaned_topic_words"],
            checkpoint["dedup_map"],
        )

    topic_ids = sorted(merged_topics.keys())
    topic_index_map = {tid: idx for idx, tid in enumerate(topic_ids)}
    sim_matrix = cosine_similarity(merged_topic_embeddings_array)
    dedup_map: Dict[str, str] = {}
    seen: set = set()

    def is_fuzzy_label_match(a: str, b: str) -> bool:
        """Determine if two labels are similar enough."""
        a, b = a.strip().lower(), b.strip().lower()
        if a == b:
            return True
        return SequenceMatcher(None, a, b).ratio() >= label_threshold

    for i in range(len(topic_ids)):
        tid_i = topic_ids[i]
        if tid_i in seen:
            continue
        for j in range(i + 1, len(topic_ids)):
            tid_j = topic_ids[j]
            if tid_j in seen:
                continue
            if is_fuzzy_label_match(topic_label[tid_i], topic_label[tid_j]):
                if sim_matrix[i][j] >= embedding_similarity_threshold:
                    canonical_tid = min(tid_i, tid_j)
                    redundant_tid = max(tid_i, tid_j)
                    dedup_map[redundant_tid] = canonical_tid
                    seen.add(redundant_tid)

    # Remove redundant topics
    for redundant_tid in dedup_map.keys():
        merged_topics.pop(redundant_tid, None)
        topic_label.pop(redundant_tid, None)
        topic_description.pop(redundant_tid, None)
        topic_words.pop(redundant_tid, None)

    # Rebuild deduplicated data
    new_merged_topics = {}
    new_topic_label = {}
    new_topic_description = {}
    new_topic_words = {}
    new_embeddings = []
    new_id_to_index = {}
    remap_ids = {}

    remaining_ids = list(merged_topics.keys())

    for new_id, tid in enumerate(remaining_ids):
        new_tid = str(new_id)
        remap_ids[tid] = new_tid
        new_merged_topics[new_tid] = merged_topics[tid]
        new_topic_label[new_tid] = topic_label[tid]
        new_topic_description[new_tid] = topic_description[tid]
        new_topic_words[new_tid] = topic_words[tid]
        new_embeddings.append(merged_topic_embeddings_array[topic_index_map[tid]])
        new_id_to_index[new_tid] = new_id

    dedup_embeddings_array = np.array(new_embeddings, dtype=np.float32)

    with open(os.path.join(model_path, "cleaned_merged_topics.pkl"), "wb") as f:
        pickle.dump(new_merged_topics, f)
    with open(os.path.join(model_path, "cleaned_topic_label.pkl"), "wb") as f:
        pickle.dump(new_topic_label, f)
    with open(os.path.join(model_path, "cleaned_topic_description.pkl"), "wb") as f:
        pickle.dump(new_topic_description, f)
    with open(os.path.join(model_path, "cleaned_topic_words.pkl"), "wb") as f:
        pickle.dump(new_topic_words, f)

    np.save(
        os.path.join(model_path, "cleaned_merged_topic_embeddings_array.npy"),
        dedup_embeddings_array,
    )

    checkpoint_data = {
        "cleaned_merged_topics": new_merged_topics,
        "cleaned_merged_topic_embeddings": dedup_embeddings_array,
        "cleaned_topic_label": new_topic_label,
        "cleaned_topic_description": new_topic_description,
        "cleaned_topic_words": new_topic_words,
        "dedup_map": dedup_map,
        "remap_ids": remap_ids,
    }
    save_checkpoint(checkpoint_path, checkpoint_data)
    logger.info(
        f"Deduplication completed. {len(dedup_map)} topics merged. {len(new_merged_topics)} topics retained."
    )

    return (
        new_merged_topics,
        dedup_embeddings_array,
        new_topic_label,
        new_topic_description,
        new_topic_words,
    )
