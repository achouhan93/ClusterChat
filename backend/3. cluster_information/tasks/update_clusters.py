import logging
from typing import Dict, Any
from opensearchpy import OpenSearch
from opensearchpy.helpers import scan, bulk

logger = logging.getLogger(__name__)


def update_cluster_paths(os_connection: OpenSearch, cluster_index_name: str) -> None:
    """
    Update the 'path' field of clusters in the OpenSearch index.

    This function reconstructs a hierarchical path for each cluster by tracing
    parent-child relationships. If the original parent-child links are missing,
    it attempts to infer the structure using the 'depth' field.

    Args:
        os_connection (OpenSearch): An OpenSearch client instance.
        cluster_index_name (str): The name of the OpenSearch index containing clusters.

    Returns:
        None
    """
    logger.info(f"Started updating the cluster path")

    # Step 1: Retrieve all clusters from the OpenSearch index

    # Initialize data structures to store cluster info and child-to-parent links
    clusters: Dict[str, Dict[str, Any]] = {}
    child_to_parent: Dict[str, str] = {}

    logger.info("Fetching all clusters from OpenSearch...")

    for hit in scan(os_connection, index=cluster_index_name):
        cluster_id = hit["_source"]["cluster_id"]
        cluster = hit["_source"]
        if not cluster_id:
            continue  # Skip malformed entries

        clusters[cluster_id] = cluster

        # Build child-to-parent mapping using the 'children' field
        for child_id in cluster.get("children", []):
            child_to_parent[child_id] = cluster_id

    # Step 2: Handle case where 'children' fields are missing or empty
    # Check if 'child_to_parent' mapping is correct
    if not child_to_parent:
        logger.error("The 'children' fields are empty or not populated correctly.")
        logger.error(
            "Attempting to build 'child_to_parent' mapping using other methods."
        )

        # Alternative method: Use 'depth' field to infer parent-child relationships
        depth_to_clusters = {}
        for cluster_id, cluster in clusters.items():
            depth = cluster.get("depth", 0)
            depth_to_clusters.setdefault(depth, []).append(cluster_id)

        # Sort depths in descending order to start from the root
        sorted_depths = sorted(depth_to_clusters.keys(), reverse=True)
        for i in range(len(sorted_depths) - 1):
            parent_depth = sorted_depths[i]
            child_depth = sorted_depths[i + 1]
            parent_clusters = depth_to_clusters[parent_depth]
            child_clusters = depth_to_clusters[child_depth]
            # Assuming that clusters at depth D+1 are children of clusters at depth D
            for child_id in child_clusters:
                # Assign the first parent cluster (you may need a better method here)
                parent_id = parent_clusters[0]
                child_to_parent[child_id] = parent_id

    # Step 3: Reconstruct 'children' fields if necessary
    # Now rebuild 'clusters' with the updated 'children' field
    for child_id, parent_id in child_to_parent.items():
        parent_cluster = clusters.get(parent_id)
        if parent_cluster:
            parent_cluster.setdefault("children", []).append(child_id)

    # Step 4: Identify root clusters (those with no parent)
    # Identify root clusters (those without parents)
    all_cluster_ids = set(clusters.keys())
    child_cluster_ids = set(child_to_parent.keys())
    root_cluster_ids = all_cluster_ids - child_cluster_ids

    if not root_cluster_ids:
        logger.error("No root clusters found. Please check the cluster data.")
        return

    # Step 5: Construct path for each cluster by walking up the tree
    # Build paths from each cluster up to the root
    logger.info("Updating paths for all clusters...")
    for cluster_id in clusters.keys():
        path = []
        current_id = cluster_id
        while True:
            path.insert(0, current_id)
            if current_id in child_to_parent:
                current_id = child_to_parent[current_id]
            else:
                # Reached a root cluster
                break
        # Convert path list to string with '/' separator
        path_str = "/".join(path)
        clusters[cluster_id]["path"] = path_str

    # Step 6: Prepare and execute bulk update in OpenSearch
    # Prepare bulk update actions
    actions = []
    for cluster_id, cluster in clusters.items():
        action = {
            "_op_type": "update",
            "_index": cluster_index_name,
            "_id": cluster_id,
            "doc": {"path": cluster["path"]},
        }
        actions.append(action)

    # Execute bulk update
    bulk(os_connection, actions)
    logger.info("Cluster paths updated successfully.")
