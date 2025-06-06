import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


def opensearch_pubmedbert_mapping() -> Dict[str, Any]:
    """
    Constructs the OpenSearch index mapping for PubMedBERT document vectors.

    Returns:
        Dict[str, Any]: A dictionary containing settings and mappings for the OpenSearch index.

    Notes:
        - This configuration enables KNN vector search using `lucene` HNSW engine.
        - The analyzer used is a custom analyzer with lowercase and preserve_original filters.
        - This mapping is suitable for semantic indexing of biomedical text embeddings.
    """
    logger.info("Generating OpenSearch mapping for PubMedBERT vector index.")

    os_mapping: Dict[str, Any] = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "modified_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "preserve_original"],
                    }
                },
                "filter": {
                    "preserve_original": {
                        "type": "word_delimiter",
                        "preserve_original": True,
                    }
                },
            },
            "knn": True,
        },
        "mappings": {
            "properties": {
                "documentSource": {"type": "keyword"},
                "documentID": {"type": "keyword"},
                "articleDate": {
                    "type": "date",
                    "format": "yyyy-MM-dd",
                },
                "title": {"type": "text", "analyzer": "modified_analyzer"},
                "journal:title": {"type": "text", "analyzer": "modified_analyzer"},
                "keywords:name": {"type": "text", "analyzer": "modified_analyzer"},
                "meshTerms": {"type": "text", "analyzer": "modified_analyzer"},
                "meshIds": {"type": "text", "analyzer": "modified_analyzer"},
                "chemicals": {"type": "text", "analyzer": "modified_analyzer"},
                "authors:name": {"type": "text", "analyzer": "modified_analyzer"},
                "authors:affiliation": {
                    "type": "text",
                    "analyzer": "modified_analyzer",
                },
                "abstract_chunk_id": {"type": "integer"},
                "abstract_chunk": {"type": "text", "analyzer": "modified_analyzer"},
                "pubmed_bert_vector": {
                    "type": "knn_vector",
                    "dimension": 768,
                    "method": {
                        "engine": "lucene",
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "parameters": {"ef_construction": 40, "m": 8},
                    },
                },
            }
        },
    }

    logger.info(
        "OpenSearch mapping for PubMedBERT vector index generated successfully."
    )
    return os_mapping
