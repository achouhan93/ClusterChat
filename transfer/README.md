# Data Transfer Scripts

This directory contains scripts for transferring the original data to an OpenSearch index. These scripts handle the extraction, transformation, and loading (ETL) of data from various sources into the OpenSearch cluster.

## Files

- `sample.json`: A sample JSON file containing structured data to be transferred.
- `scripts/push_metadata.py`: A script for transferring metadata to an OpenSearch index. Input is a JSON file containing structured data `data/arxiv-metadata-oai-snapshot.json`. Output is the OpenSearch index where the metadata is stored `frameintell_arxiv_metadata`.
- `pull_topic_embeddings.ipynb`: A Jupyter notebook for pulling topic embeddings from OpenSearch to a JSON file for cluster analysis. Input is the OpenSearch index where the embeddings are stored, in this case `frameintell_arxiv_embeddings`. Output is a JSON file containing the embeddings `data/topic_embeddings.json` for a given topic. The topic selected for this practical is "Machine Learning".

## About the push_metadata.py script
1. Connect to OpenSearch:  
Establishes a connection to an OpenSearch instance using the OpenSearch client from the opensearch-py library.
2. Define Index Mapping:  
Specifies the structure and data types for the fields in the OpenSearch index, including properties like id, submitter, authors, title, abstract, and more.
3. Create Index:  
Checks if the specified index (frameintell_arxiv_metadata) exists. If not, it creates the index using the defined mappings.
4. Bulk Index Data:  
Reads data from a JSON file (data/arxiv-metadata-oai-snapshot.json) line by line.  
Prepares the data for bulk indexing by creating a list of operations and documents.  
Periodically sends batches of data to OpenSearch for indexing.  
Ensures any remaining data is indexed after the loop completes.  
5. Count and Search Documents:  
Queries the OpenSearch index to count the number of documents indexed and searches for matching a specific term for validating purposes.

## Index Mapping Definition
The index mapping used for the OpenSearch index `frameintell_arxiv_metadata` is the following:  
```python
mappings = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "submitter": {"type": "text"},
            "authors": {"type": "text"},
            "title": {"type": "text"},
            "comments": {"type": "text"},
            "journal-ref": {"type": "text"},
            "doi": {"type": "keyword"},
            "report-no": {"type": "keyword", "null_value": "null"},
            "categories": {"type": "text"},
            "license": {"type": "keyword", "null_value": "null"},
            "abstract": {"type": "text", "analyzer": "english"},
            "versions": {
                "type": "nested",
                "properties": {
                    "version": {"type": "keyword"},
                    "created": {"type": "date", "format": "EEE, d MMM yyyy HH:mm:ss 'GMT'"},
                },
            },
            "update_date": {"type": "date", "format": "yyyy-MM-dd"},
        }
    }
}
```

## Explanation of the Metadata Mapping

- **id**: Mapped as `keyword` because it is a unique identifier for each paper.
- **submitter**: Mapped as `text` to allow for full-text search.
- **authors**: Mapped as `text` to enable full-text search. This field includes the list of authors in a single string.
- **title**: Mapped as `text` with the `standard` analyzer for effective full-text search.
- **comments**: Mapped as `text` since it contains free-form text.
- **journal-ref**: Mapped as `text` to allow full-text search, as journal references can vary widely.
- **doi**: Mapped as `keyword` because it is a unique identifier.
- **report-no**: Mapped as `keyword` because it is a unique identifier.
- **categories**: Mapped as `keyword` since categories/tags are usually predefined and exact matches are useful.
- **license**: Mapped as `keyword` with a `null_value` set to "null" to handle null values appropriately.
- **abstract**: Mapped as `text` with the `english` analyzer to optimize search for English text.
- **versions**: Mapped as `nested` type to handle multiple versions of a paper. Each version has:
  - **version**: Mapped as `keyword` since it's an identifier.
  - **created**: Mapped as `date` with a custom format to handle the provided date string.
- **update_date**: Mapped as `date` with the format `yyyy-MM-dd`.

This mapping ensures that each field in the ArXiv metadata is indexed correctly for optimal search performance and data integrity.

## Additional Files

The following two files are for testing but not necessariy for the final version.
- `push_cleaned_text.py`: A script for transferring cleaned text data to an OpenSearch index.
- `push_authors.py`: A script for transferring author data to an OpenSearch index.

## Usage
1. Run the transfer script:
    ```sh
    python transfer/push_metadata.py
    ```