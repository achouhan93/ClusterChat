from opensearchpy.helpers import scan, bulk
import logging

log = logging.getLogger(__name__)

def update_cluster_paths(os_connection, cluster_index_name):
    """
    Updates the 'path' field for each cluster in the OpenSearch index,
    reconstructing the path from the root (highest depth) down to each node.

    Args:
        os_connection (OpenSearch): The OpenSearch client connection.
        cluster_index_name (str): The name of the cluster index in OpenSearch.
    """
    log.info(f"Started updating the cluster path")
    # Step 1: Retrieve all clusters from the OpenSearch index
    clusters = {}
    child_to_parent = {}

    log.info("Fetching all clusters from OpenSearch...")
    for hit in scan(os_connection, index=cluster_index_name):
        cluster_id = hit["_source"]["cluster_id"]
        cluster = hit["_source"]
        clusters[cluster_id] = cluster
        # Build child-to-parent mapping using the 'children' field
        for child_id in cluster.get("children", []):
            child_to_parent[child_id] = cluster_id

    # Check if 'child_to_parent' mapping is correct
    if not child_to_parent:
        log.error("The 'children' fields are empty or not populated correctly.")
        log.error("Attempting to build 'child_to_parent' mapping using other methods.")
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

    # Now rebuild 'clusters' with the updated 'children' field
    for child_id, parent_id in child_to_parent.items():
        parent_cluster = clusters.get(parent_id)
        if parent_cluster:
            parent_cluster.setdefault("children", []).append(child_id)

    # Identify root clusters (those without parents)
    all_cluster_ids = set(clusters.keys())
    child_cluster_ids = set(child_to_parent.keys())
    root_cluster_ids = all_cluster_ids - child_cluster_ids

    if not root_cluster_ids:
        log.error("No root clusters found. Please check the cluster data.")
        return

    # Build paths from each cluster up to the root
    log.info("Updating paths for all clusters...")
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
    log.info("Cluster paths updated successfully.")

