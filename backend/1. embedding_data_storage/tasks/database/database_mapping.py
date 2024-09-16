def opensearch_pubmedbert_mapping():
    # """"""""""
    # Functionality: Creation of the mapping for the ElasticSearch or OpenSearch Index
    #
    # For this project mapping is created from JSON using https://json-to-es-mapping.netlify.app/
    #
    # Signature of the function:
    #  Input:
    #       No input is required for this function, as it is executed to create an object for mapping
    #
    #  Output:
    #       os_mapping: Mapping setting for the ElasticSearch or OpenSearch Index
    # """"""""""
    os_mapping = {
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
                        "engine": "nmslib",
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "parameters": {"ef_construction": 40, "m": 8},
                    },
                },
            }
        },
    }

    return os_mapping
