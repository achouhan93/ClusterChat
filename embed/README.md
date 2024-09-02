# Generate Embeddings Script for arXiv Papers

This script generates embeddings for abstracts of arXiv papers using the Sentence Transformers library and stores these embeddings in an OpenSearch index. The script processes, generates and stores the embeddings based on the timestamp (`update_date` parameter) of the arXiv papers. It processes the documents in batches, starting from the latest documents and moving towards the oldest ones. By default, it processes 1000 documents in each batch starting from the latest documents available in the OpenSearch index till the oldest ones. The start and end timestamps can be configured in the script, so that users can generate embeddings for a specific time range.

## How to Run the Script

1. **Configure Logging:**
   The script will automatically log its activities and errors to `embedding_generation.log`.

2. **OpenSearch Connection:**
   The script connects to an OpenSearch instance. Ensure that the following information is provided:
   - `host`: OpenSearch host. Set to `opensearch-ds.ifi.uni-heidelberg.de`.
   - `port`: OpenSearch port. Set to `443`.
   - `username`: OpenSearch account username.
   - `password`: OpenSearch account password.

3. **Configure parameters:**  
    The following parameters can be configured in the script:
   - `source_index`: Name of the source index containing arXiv metadata. Set to `frameintell_arxiv_metadata`.
   - `target_index`: Name of the target index where embeddings will be stored. Set to `frameintell_arxiv_embeddings`.
   - `model_name`: Name of the Sentence Transformer model to use. Set to `Alibaba-NLP/gte-large-en-v1.5`.
   - `batch_size`: Number of documents to process in each batch. Set to `1000`.
   - `dimension`: Dimension of the embedding vector. Set to `1024`.

4. **Run the Script:**

```bash
python process/generate_embeddings_server.py
```

## What the Script Does

1. Connects to the OpenSearch cluster using the provided credentials.
2. Creates a Point in Time (PIT) context to maintain consistency during batch processing.
3. Retrieves the oldest update date from the source index to use as the end date for processing.
4. Creates the target index with appropriate mappings if it doesn't exist.
5. Loads the specified Sentence Transformer model and NLTK stopwords.
6. Processes documents in batches:
   - Fetches a batch of documents from the source index.
   - Processes the abstracts by removing special characters, converting to lowercase, and removing stopwords.
   - Generates embeddings for the processed abstracts using the Sentence Transformer model.
   - Bulk inserts the processed documents with their embeddings into the target index.
7. Logs progress and any errors to a file named `embedding_generation.log`.
8. Continues processing until all documents within the specified date range have been processed.
9. Cleans up by deleting the PIT context and closing the OpenSearch connection.

The script uses a default batch size of 1000 documents and keeps the PIT context alive for 60 minutes to handle large batches. You can adjust these parameters in the script if needed.

Note: Make sure you have sufficient permissions to read from the source index and write to the target index in your OpenSearch cluster.

## Additional Information

- The script uses OpenSearch's Point in Time (PIT) API to maintain a consistent view of the data during the search operations.
- The embeddings are generated using the `sentence-transformers` library, which supports various pre-trained models.
- The target index mapping that is created in case it doesn't exist includes the following fields:
   - `id`: Unique identifier for the document.
   - `abstract`: Original abstract from the metadata.
   - `processed_abstract`: Abstract after processing.
   - `embedding`: Embedding vector generated for the abstract.
   - `update_date`: Timestamp of the document.

```python
    mappings = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "abstract": {"type": "text"},
                "processed_abstract": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dimension,
                },
                "update_date": {"type": "date"},
            }
        }
    }
```