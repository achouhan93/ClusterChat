import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import logging
import json
from openai import OpenAI
from utils import load_config_from_env
import pickle
import os
from time import sleep
import math
from tqdm import tqdm

CONFIG = load_config_from_env()
log = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def get_cluster_metadata(child_labels, child_descriptions):

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
    try:
        metadata = json.loads(content)
    except Exception as e:
        metadata = {
            "label": None,
            "description": None,
            "error": f"Failed to parse JSON: {e}",
            "raw_output": content,
        }

    return metadata


def save_checkpoint(checkpoint_path, checkpoint_data):
    """Saves the current checkpoint data to a file."""
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_data, f)
    log.info(f"Checkpoint saved at {checkpoint_path}.")


def load_checkpoint(checkpoint_path):
    """Loads checkpoint data from a file."""
    with open(checkpoint_path, "rb") as f:
        checkpoint_data = pickle.load(f)
    log.info(f"Checkpoint loaded from {checkpoint_path}.")
    return checkpoint_data


def build_custom_hierarchy(
    merged_topic_embeddings_array,
    merged_topics,
    topic_label,
    topic_description,
    topic_words,
    umap_model,
    model_path,
):
    """
    Build a hierarchy of clusters up to a specified depth.
    At each level, clusters are merged into pairs to achieve the desired depth.
    """
    depth = math.ceil(math.log2(len(merged_topics))) + 1
    checkpoint_path = os.path.join(model_path, "checkpoint.pkl")
    log.info("Building the topic hierarchy using agglomerative clustering")

    if os.path.exists(checkpoint_path):
        checkpoint = load_checkpoint(checkpoint_path)
        clusters = checkpoint["clusters"]
        cluster_embeddings = checkpoint["cluster_embeddings"]
        linkage_matrix = checkpoint.get("linkage_matrix", [])
        completed_merge_id = checkpoint.get("completed_merge_id", -1)
        log.info(f"Resuming from checkpoint at merge_id={completed_merge_id}")
    else:
        clusters = {}
        cluster_embeddings = {}
        completed_merge_id = -1
        current_topic_ids = list(merged_topics.keys())

        for i, tid in tqdm(enumerate(current_topic_ids), 
                           total=len(current_topic_ids), 
                           desc="Initializing leaf clusters"
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
        max([int(k.replace("cluster_", "")) if "cluster_" in k else int(k)
             for k in clusters.keys()]) + 1
    )

    for merge_id, (left_idx, right_idx) in tqdm(
        enumerate(linkage_matrix), 
        total=len(linkage_matrix), 
        desc="Merging Clusters"
        ):
        if merge_id <= completed_merge_id:
            continue

        cid_i = (
            str(left_idx) if str(left_idx) in clusters else f"cluster_{left_idx}"
        )
        cid_j = (
            str(right_idx) if str(right_idx) in clusters else f"cluster_{right_idx}"
        )

        if cid_i not in clusters or cid_j not in clusters:
            log.warning(f"Skipping merge {merge_id}: missing clusters {cid_i} or {cid_j}")
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
        new_embedding = (
            cluster_embeddings[cid_i] + cluster_embeddings[cid_j]
        ) / 2

        new_path = clusters[cid_i]["path"] + "/" + clusters[cid_j]["path"]
        full_path = new_cluster_id + "/" + new_path

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

    similarity_matrix = cosine_similarity(np.array(list(cluster_embeddings.values())))
    cluster_ids = list(cluster_embeddings.keys())

    for i, cluster_id_i in enumerate(cluster_ids):
        clusters[cluster_id_i]["pairwise_similarity"] = {}
        for j, cluster_id_j in enumerate(cluster_ids):
            if i != j:
                clusters[cluster_id_i]["pairwise_similarity"][cluster_id_j] = (
                    similarity_matrix[i, j]
                )

    log.info("Hierarchy construction with depth control completed")

    max_depth = max(cluster["depth"] for cluster in clusters.values())
    log.info(f"Final hierarchy depth: {max_depth}")

    root_cluster = max(clusters.values(), key=lambda c: c["depth"])
    log.info(f"Root cluster ID: {root_cluster['cluster_id']}, depth: {root_cluster['depth']}")

    with open(os.path.join(model_path, "clusters.pkl"), "wb") as f:
        pickle.dump(clusters, f)

    with open(os.path.join(model_path, "cluster_embeddings.pkl"), "wb") as f:
        pickle.dump(cluster_embeddings, f)

    log.info("Final clusters saved with depth restriction")

    return clusters, cluster_embeddings