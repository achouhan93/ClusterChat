"""
Module for hierarchical clustering and metadata generation using OpenAI.
"""

import os
import gc
import math
import json
import pickle
import logging
from time import sleep
from typing import Dict, Tuple, List, Any

import numpy as np
from tqdm import tqdm
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

from utils import load_config_from_env

# Initialize logging and config
logger = logging.getLogger(__name__)
CONFIG = load_config_from_env()
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def get_cluster_metadata(
    child_labels: List[str], child_descriptions: List[str]
) -> Dict[str, Any]:
    """
    Generate metadata (label and description) for a parent cluster using OpenAI.

    Args:
        child_labels (List[str]): List of child cluster labels.
        child_descriptions (List[str]): Corresponding descriptions for child clusters.

    Returns:
        Dict[str, Any]: Dictionary with keys: 'label', 'description'. May include error details.
    """
    # Build explicit pairings: Topic 1: Label – Description
    topic_blocks = [
        f"Topic {i+1}: {label} – {desc}"
        for i, (label, desc) in enumerate(zip(child_labels, child_descriptions))
    ]
    topics_str = "\n".join(topic_blocks)

    prompt = (
        f"You are given several topics and their descriptions:\n\n"
        f"{topics_str}\n\n"
        f"Generate a JSON object with:\n"
        f"- 'label': A concise topic label using **at most three words**, summarizing the topic clearly. Do not use punctuation.\n"
        f"- 'description': A short informative sentence of **at most 15 words** that summarizes the combined meaning of all topics.\n\n"
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
        logger.warning(f"OpenAI metadata generation failed: {e}")
        return {
            "label": None,
            "description": None,
            "error": f"Failed to parse JSON: {e}",
            "raw_output": content,
        }


def save_checkpoint(checkpoint_path: str, checkpoint_data: Dict[str, Any]) -> None:
    """
    Save checkpoint data to a file.

    Args:
        checkpoint_path (str): Path to save the checkpoint.
        checkpoint_data (Dict[str, Any]): Dictionary containing checkpoint information.
    """
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_data, f)

    logger.info(f"Checkpoint saved at {checkpoint_path}.")


def load_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    """
    Load checkpoint data from a file.

    Args:
        checkpoint_path (str): Path to the checkpoint file.

    Returns:
        Dict[str, Any]: Loaded checkpoint data.
    """
    with open(checkpoint_path, "rb") as f:
        checkpoint = pickle.load(f)
    logger.info(f"Checkpoint loaded from {checkpoint_path}")
    return checkpoint


def build_custom_hierarchy(
    merged_topic_embeddings_array: np.ndarray,
    merged_topics: Dict[str, Any],
    topic_label: Dict[str, str],
    topic_description: Dict[str, str],
    topic_words: Dict[str, List[str]],
    umap_model: Any,
    model_path: str,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Build a hierarchical clustering structure from initial topic embeddings.

    Args:
        merged_topic_embeddings_array (np.ndarray): Initial topic embeddings.
        merged_topics (Dict[str, Any]): Topic data for each cluster.
        topic_label (Dict[str, str]): Labels for each topic.
        topic_description (Dict[str, str]): Descriptions for each topic.
        topic_words (Dict[str, List[str]]): Word lists for each topic.
        umap_model (Any): Pretrained UMAP model.
        model_path (str): Directory to save checkpoints and outputs.

    Returns:
        Tuple[Dict[str, Any], Dict[str, np.ndarray]]: Final cluster dictionary and embeddings.
    """
    logger.info("Starting hierarchical clustering process.")
    depth = math.ceil(math.log2(len(merged_topics))) + 1
    checkpoint_path = os.path.join(model_path, "checkpoint.pkl")

    if os.path.exists(checkpoint_path):
        checkpoint = load_checkpoint(checkpoint_path)
        clusters = checkpoint["clusters"]
        cluster_embeddings = checkpoint["cluster_embeddings"]
        linkage_matrix = checkpoint.get("linkage_matrix", [])
        completed_merge_id = checkpoint.get("completed_merge_id", -1)
        logger.info(f"Resuming from checkpoint at merge_id: {completed_merge_id}")
    else:
        clusters = {}
        cluster_embeddings = {}
        completed_merge_id = -1
        current_topic_ids = list(merged_topics.keys())

        # Initialize leaf nodes
        for i, tid in tqdm(
            enumerate(current_topic_ids),
            total=len(current_topic_ids),
            desc="Initializing clusters",
        ):
            clusters[str(tid)] = {
                "cluster_id": str(tid),
                "label": topic_label[tid],
                "topic_information": merged_topics[tid],
                "topic_words": topic_words[tid],
                "description": topic_description[tid],
                "is_leaf": True,
                "depth": 0,
                "path": str(tid),
                "x": float(0),
                "y": float(0),
                "children": [],
                "size": 1,
            }
            cluster_embeddings[str(tid)] = merged_topic_embeddings_array[i]

        # Apply UMAP to get x and y coordinates
        topic_umap_embeddings = umap_model.transform(merged_topic_embeddings_array)
        for i, tid in enumerate(current_topic_ids):
            clusters[str(tid)]["x"] = float(topic_umap_embeddings[i][0])
            clusters[str(tid)]["y"] = float(topic_umap_embeddings[i][1])

        agg = AgglomerativeClustering(
            n_clusters=None, distance_threshold=0.0, metric="cosine", linkage="average"
        )
        agg.fit(merged_topic_embeddings_array)
        linkage_matrix = agg.children_

    current_cluster_index = (
        max(
            [
                int(k.replace("cluster_", "")) if "cluster_" in k else int(k)
                for k in clusters.keys()
            ]
        )
        + 1
    )

    for merge_id, (left_idx, right_idx) in tqdm(
        enumerate(linkage_matrix), total=len(linkage_matrix), desc="Merging Clusters"
    ):
        if merge_id <= completed_merge_id:
            continue

        cid_i = str(left_idx) if str(left_idx) in clusters else f"cluster_{left_idx}"
        cid_j = str(right_idx) if str(right_idx) in clusters else f"cluster_{right_idx}"

        if cid_i not in clusters or cid_j not in clusters:
            logger.warning(
                f"Skipping merge {merge_id}: missing clusters {cid_i} or {cid_j}"
            )
            continue

        new_depth = max(clusters[cid_i]["depth"], clusters[cid_j]["depth"]) + 1
        child_labels = [clusters[cid_i]["label"], clusters[cid_j]["label"]]
        child_descriptions = [
            clusters[cid_i]["description"],
            clusters[cid_j]["description"],
        ]

        metadata = get_cluster_metadata(child_labels, child_descriptions)
        combined_label = metadata.get("label")
        combined_description = metadata.get("description")
        sleep(2)

        new_cluster_id = f"cluster_{current_cluster_index}"
        current_cluster_index += 1

        size_i = clusters[cid_i]["size"]
        size_j = clusters[cid_j]["size"]
        total_size = size_i + size_j

        avg_x = (
            size_i * clusters[cid_i]["x"] + size_j * clusters[cid_j]["x"]
        ) / total_size
        avg_y = (
            size_i * clusters[cid_i]["y"] + size_j * clusters[cid_j]["y"]
        ) / total_size
        new_embedding = (cluster_embeddings[cid_i] + cluster_embeddings[cid_j]) / 2

        full_path = (
            f"{new_cluster_id}/{clusters[cid_i]['path']}/{clusters[cid_j]['path']}"
        )
        combined_topic_words = list(
            set(clusters[cid_i]["topic_words"] + clusters[cid_j]["topic_words"])
        )

        clusters[new_cluster_id] = {
            "cluster_id": new_cluster_id,
            "label": combined_label,
            "topic_information": None,
            "description": combined_description,
            "topic_words": combined_topic_words,
            "is_leaf": False,
            "depth": new_depth,
            "path": full_path,
            "x": avg_x,
            "y": avg_y,
            "children": [cid_i, cid_j],
            "size": total_size,
        }

        cluster_embeddings[new_cluster_id] = new_embedding

        # Save after each merge
        checkpoint_data = {
            "clusters": clusters,
            "cluster_embeddings": cluster_embeddings,
            "linkage_matrix": linkage_matrix,
            "completed_merge_id": merge_id,
        }
        save_checkpoint(checkpoint_path, checkpoint_data)
        sleep(2)

    logger.info("Computing pairwise cosine similarities.")
    similarity_matrix = cosine_similarity(np.array(list(cluster_embeddings.values())))
    cluster_ids = list(cluster_embeddings.keys())

    for i, cluster_id_i in enumerate(cluster_ids):
        clusters[cluster_id_i]["pairwise_similarity"] = {}
        for j, cluster_id_j in enumerate(cluster_ids):
            if i != j:
                clusters[cluster_id_i]["pairwise_similarity"][cluster_id_j] = (
                    similarity_matrix[i, j]
                )

    logger.info("Hierarchy construction with depth control completed")

    max_depth = max(cluster["depth"] for cluster in clusters.values())
    root_cluster = max(clusters.values(), key=lambda c: c["depth"])
    logger.info(f"Final hierarchy depth: {max_depth}")
    logger.info(
        f"Root cluster ID: {root_cluster['cluster_id']}, depth: {root_cluster['depth']}"
    )

    with open(os.path.join(model_path, "clusters.pkl"), "wb") as f:
        pickle.dump(clusters, f)

    with open(os.path.join(model_path, "cluster_embeddings.pkl"), "wb") as f:
        pickle.dump(cluster_embeddings, f)

    logger.info("Final clusters saved with depth restriction")

    return clusters, cluster_embeddings
