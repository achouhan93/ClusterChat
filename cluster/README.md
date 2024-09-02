# Clustering Analysis

This directory contains scripts and data for performing clustering analysis on arXiv papers. The clustering is primarily done using UMAP for dimensionality reduction and HDBSCAN for clustering. The input of the `cluster_hdbscan.py` file is `data/embeddings_data.jsonl` after having generated the embeddings. The output is a CSV file containing the clustered data in two dimensions for further use in the web application.

## Files

- [`cluster_hdbscan.py`](cluster_hdbscan.py): Script for performing clustering using HDBSCAN.
- [`pca_hdbscan_pca.csv`](pca_hdbscan_pca.csv): CSV file containing PCA-reduced data clustered with HDBSCAN and PCA reduction to two dimensions.
- [`pca_hdbscan_umap.csv`](pca_hdbscan_umap.csv): CSV file containing UMAP-reduced data clustered with HDBSCAN and UMAP reduction to two dimensions.
- [`umap_hdbscan_pca.csv`](umap_hdbscan_pca.csv): CSV file containing PCA-reduced data clustered with UMAP and HDBSCAN and PCA reduction to two dimensions.
- [`umap_hdbscan_umap.csv`](umap_hdbscan_umap.csv): CSV file containing UMAP-reduced data clustered with UMAP and HDBSCAN and UMAP reduction to two dimensions.  

## Approach to Clustering High-Dimensional Text Data

1. **PCA followed by HDBSCAN and then reduce to two dimensions with PCA**:
    - **PCA** (Principal Component Analysis) is a linear dimensionality reduction technique that can help in reducing the dimensionality of your data while retaining as much variance as possible.
    - **HDBSCAN** (Hierarchical Density-Based Spatial Clustering of Applications with Noise) is a robust clustering algorithm that works well with varying densities and can identify noise points.
    - **Second PCA**: Reducing the data to two dimensions can help in visualization but might not be as informative due to the initial linear reduction.

2. **UMAP followed by HDBSCAN and then reduce to two dimensions with UMAP**:
    - **UMAP** (Uniform Manifold Approximation and Projection) is a nonlinear dimensionality reduction technique that preserves the local and global structure of the data better than PCA.
    - **HDBSCAN** can then be applied to the lower-dimensional space to find clusters.
    - **Second UMAP**: Reducing to two dimensions for visualization while keeping the non-linear relationships intact.

3. **A combination of the above two**:
    - Combining PCA and UMAP might capture both linear and nonlinear relationships, potentially leading to better clustering results.

## UMAP followed by HDBSCAN and Visualization with UMAP is a good choice  

**Why?**
1. **Preservation of Data Structure**: UMAP excels at preserving both local and global structures in the data, which is crucial for high-dimensional text data where relationships might be complex and nonlinear.
2. **Robust Clustering**: HDBSCAN is highly suitable for clustering in lower-dimensional spaces obtained via UMAP. It handles varying densities and identifies noise, making it well-suited for real-world datasets like yours.
3. **Visualization**: Reducing to two dimensions with UMAP ensures that the visualization step maintains the non-linear relationships, providing more meaningful insights into the cluster structure.  

When using embeddings derived from a language model with a dimensionality of 1024, the goal of reducing dimensions with UMAP before applying HDBSCAN is to strike a balance between retaining meaningful information and reducing computational complexity.

## Dimensionality Reduction: Reduce to 50 Dimensions  

**Why?**
1. **Balancing Information Retention and Computational Efficiency**:
   - Reducing to too few dimensions (e.g., 2 or 3) might result in losing important information about the relationships between data points.
   - Reducing to too many dimensions (e.g., 100 or more) might retain more information but can be computationally expensive and might not significantly improve clustering quality.

2. **Empirical Evidence**:
   - Research and empirical evidence suggest that reducing high-dimensional data (e.g., 1024) to a mid-range dimensionality (e.g., 30-50) with UMAP often retains sufficient information for effective clustering while significantly reducing computational load.

3. **Clustering Accuracy**:
   - HDBSCAN is designed to work well with data that has been effectively reduced in dimensions while preserving density-based structures. A dimensionality of around 50 usually strikes a good balance, allowing HDBSCAN to identify clusters accurately. Using 50 dimensions also vastly improves the HDBSCAN speed compared to the original 1024 dimensions. 
   
## HDBSCAN Parameters

1. **min_cluster_size**: 30-100
   - **Reasoning**: `min_cluster_size` determines the smallest size a cluster can be. For a large dataset like yours, starting with 30 to 100 is reasonable as it ensures that smaller, potentially meaningful clusters can still be identified without overfragmenting the data.
   - **Start with**: 30, 50, and 100. Evaluate the coherence and significance of the clusters formed.

2. **min_samples**: Similar to or slightly lower than `min_cluster_size` (e.g., 20-80)
   - **Reasoning**: `min_samples` influences the robustness of the clusters. Setting it similar to `min_cluster_size` helps in ensuring that the clusters are not overly sensitive to noise and outliers. For example, if `min_cluster_size` is 50, you might start with `min_samples` at 40.
   - **Start with**: Values such as 20, 40, and 80, and adjust based on the noise level and cluster stability you observe.


##  Used Configuration
1. **HDBSCAN**:
   - `min_cluster_size` = 50
   - `min_samples` = 50
