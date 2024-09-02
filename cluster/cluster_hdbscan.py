import json
import hdbscan
import numpy as np
import pandas as pd
from umap import UMAP
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Load data
print("Loading data...")
data = []
with open("data/embeddings_data.jsonl", "r") as file:
    for line in tqdm(file):
        data.append(json.loads(line))

# Extract embeddings and IDs
ids = [item["id"] for item in data]
embeddings = np.array([item["embedding"] for item in data])

# First UMAP reduction
print("Performing initial UMAP reduction...")
umap_reducer = UMAP(n_components=50)
embeddings_50D = umap_reducer.fit_transform(embeddings)

# Perform PCA reduction
# print("Performing initial PCA reduction...")
# pca_reducer = PCA(n_components=50)
# embeddings_50D = pca_reducer.fit_transform(embeddings)

# HDBSCAN clustering
print("Performing HDBSCAN clustering...")
clusterer = hdbscan.HDBSCAN(min_cluster_size=50, min_samples=50)
cluster_labels = clusterer.fit_predict(embeddings_50D)

# Second UMAP reduction for visualization
# print("Performing final UMAP reduction for visualization...")
# umap_reducer_2d = UMAP(n_components=2)
# embeddings_2D = umap_reducer_2d.fit_transform(embeddings_50D)

# Perform PCA reduction for visualization
print("Performing PCA reduction for visualization...")
pca_reducer = PCA(n_components=2)
embeddings_2D = pca_reducer.fit_transform(embeddings_50D)

# Plotting
print("Generating plot...")
plt.figure(figsize=(20, 20))
scatter = plt.scatter(
    embeddings_2D[:, 0],
    embeddings_2D[:, 1],
    c=cluster_labels,
    cmap="viridis",
    s=1,
    alpha=0.75,
)
plt.colorbar(scatter)
plt.title("arXiv Abstracts Clustering Visualization")
plt.savefig("arxiv_clusters_visualization.png", dpi=500, bbox_inches="tight")
plt.close()

# Save results
print("Saving results...")
results = pd.DataFrame(
    {
        "id": ids,
        "cluster": cluster_labels,
        "x": embeddings_2D[:, 0],
        "y": embeddings_2D[:, 1],
    }
)
results.to_csv("arxiv_clustering_results.csv", index=False)

print(
    "Process completed. Results saved in 'arxiv_clustering_results.csv' and visualization in 'arxiv_clusters_visualization.png'."
)
