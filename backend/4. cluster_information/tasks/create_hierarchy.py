import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from openai import OpenAI
from utils import load_config_from_env

CONFIG = load_config_from_env()
log = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

def get_cluster_label(child_labels):
    prompt = f"Generate a concise and informative label of two words for a cluster that combines the following topics: {', '.join(child_labels)}."
    # Call the OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Or another suitable model you have access to
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates concise topic labels of two words.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=10,
        n=1,
        temperature=0.1,
    )
    description = response.choices[0].message.content.strip()
    return description


def get_cluster_description(child_labels, child_descriptions):
    """
    Generate a descriptive summary for the new cluster based on its child clusters' labels and descriptions.
    """
    prompt = (
        f"Provide a brief, descriptive summary for a cluster that combines the following topics: "
        f"{', '.join(child_labels)}. The topics have the following descriptions: {', '.join(child_descriptions)}."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates concise topic descriptions.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=20,
        n=1,
        temperature=0.5,
    )
    description = response.choices[0].message.content.strip()
    return description


def build_custom_hierarchy(
    merged_topic_embeddings_array,
    merged_topics,
    topic_label,
    topic_description,
    topic_words,
    umap_model,
    depth=9,
):
    """
    Build a hierarchy of clusters up to a specified depth.
    At each level, clusters are merged into pairs to achieve the desired depth.
    """
    log.info(f"Building the topic hierarchy started")
    # Initialize clusters
    clusters = {}
    cluster_embeddings = {}
    current_topic_ids = list(merged_topics.keys())

    for i, tid in enumerate(current_topic_ids):
        clusters[str(tid)] = {
            "cluster_id": str(tid),
            "label": topic_label[tid],
            "topic_information": merged_topics[tid],
            "topic_words": topic_words[tid],  # Store associated topic words
            "description": topic_description[tid],
            "is_leaf": True,
            "depth": 0,
            "path": str(tid),
            "x": float(0),  # Placeholder, will be updated later
            "y": float(0),  # Placeholder, will be updated later
            "children": [],
        }
        cluster_embeddings[str(tid)] = merged_topic_embeddings_array[i]

    # Apply UMAP to get x and y coordinates
    topic_umap_embeddings = umap_model.transform(merged_topic_embeddings_array)
    for i, tid in enumerate(current_topic_ids):
        clusters[str(tid)]["x"] = float(topic_umap_embeddings[i][0])
        clusters[str(tid)]["y"] = float(topic_umap_embeddings[i][1])

    # Sort current_clusters in descending order of topic IDs
    current_clusters = list(clusters.keys())

    for current_depth in range(1, depth + 1):
        new_clusters = []
        num_clusters = len(current_clusters)
        i = 0

        while i < num_clusters:
            cid_i = current_clusters[i]
            if i + 1 < num_clusters:
                cid_j = current_clusters[i + 1]

                # Generate label and description for the new parent cluster
                child_labels = [clusters[cid_i]["label"], clusters[cid_j]["label"]]
                combined_label = get_cluster_label(child_labels)

                child_descriptions = [
                    clusters[cid_i]["description"],
                    clusters[cid_j]["description"],
                ]
                combined_description = get_cluster_description(
                    child_labels, child_descriptions
                )

                # Merge clusters cid_i and cid_j
                new_cluster_id = f"cluster_{len(clusters)}"

                # Compute average coordinates
                avg_x = (clusters[cid_i]["x"] + clusters[cid_j]["x"]) / 2
                avg_y = (clusters[cid_i]["y"] + clusters[cid_j]["y"]) / 2
                new_embedding = (
                    cluster_embeddings[cid_i] + cluster_embeddings[cid_j]
                ) / 2

                # Combine paths
                new_path = clusters[cid_i]["path"] + "/" + clusters[cid_j]["path"]
                full_path = new_cluster_id + "/" + new_path

                # Combine unique topic words
                combined_topic_words = list(
                    set(clusters[cid_i]["topic_words"] + clusters[cid_j]["topic_words"])
                )

                # Create new cluster
                clusters[new_cluster_id] = {
                    "cluster_id": new_cluster_id,
                    "label": combined_label,
                    "topic_information": None,
                    "description": combined_description,
                    "topic_words": combined_topic_words,
                    "is_leaf": False,
                    "depth": current_depth,
                    "path": full_path,
                    "x": avg_x,
                    "y": avg_y,
                    "children": [cid_i, cid_j],
                }

                # Update Cluster Embeddings
                cluster_embeddings[new_cluster_id] = new_embedding
                new_clusters.append(new_cluster_id)
                i += 2
            else:
                # If odd number of clusters, the last one remains unmerged
                clusters[cid_i]["depth"] = current_depth
                new_clusters.append(cid_i)
                i += 1

        current_clusters = new_clusters
        if len(current_clusters) == 1:
            # Reached the root
            break

    # Calculate pairwise similarity for each cluster in final structure
    similarity_matrix = cosine_similarity(np.array(list(cluster_embeddings.values())))
    cluster_ids = list(cluster_embeddings.keys())

    # Store similarity information between each cluster pair
    for i, cluster_id_i in enumerate(cluster_ids):
        clusters[cluster_id_i]["pairwise_similarity"] = {}
        for j, cluster_id_j in enumerate(cluster_ids):
            if i != j:
                clusters[cluster_id_i]["pairwise_similarity"][cluster_id_j] = (
                    similarity_matrix[i, j]
                )
    
    log.info(f"Building the topic hierarchy completed")

    return clusters, cluster_embeddings
