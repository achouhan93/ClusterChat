def opensearch_complete_mapping():
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
        },
        "mappings": {
            "properties": {
                "abstract": {"type": "text", "analyzer": "modified_analyzer"},
                "articleDate": {
                    "type": "date",
                    "format": "yyyy-MM-dd",
                    "null_value": "1900-01-01",
                },
                "authors": {
                    "type": "nested",
                    "properties": {
                        "affiliations": {
                            "type": "nested",
                            "properties": {
                                "institute": {
                                    "type": "text",
                                    "analyzer": "modified_analyzer",
                                }
                            },
                        },
                        "firstName": {"type": "keyword", "null_value": "NONE"},
                        "lastName": {"type": "keyword", "null_value": "NONE"},
                    },
                },
                "chemicals": {
                    "type": "nested",
                    "properties": {
                        "chemicalMeshID": {"type": "keyword", "null_value": "NONE"},
                        "name": {"type": "text", "analyzer": "modified_analyzer"},
                    },
                },
                "fullText": {"type": "text", "analyzer": "modified_analyzer"},
                "fullTextURL": {"type": "keyword", "null_value": "NONE"},
                "grants": {
                    "type": "nested",
                    "properties": {
                        "acronym": {"type": "keyword", "null_value": "NONE"},
                        "agency": {"type": "keyword", "null_value": "NONE"},
                        "country": {"type": "keyword", "null_value": "NONE"},
                        "grantID": {"type": "keyword", "null_value": "NONE"},
                    },
                },
                "history": {
                    "type": "nested",
                    "properties": {
                        "date": {
                            "type": "date",
                            "format": "yyyy-MM-dd",
                            "null_value": "1900-01-01",
                        },
                        "type": {"type": "keyword", "null_value": "NONE"},
                    },
                },
                "journalInformation": {
                    "type": "nested",
                    "properties": {
                        "journalTitle": {
                            "type": "text",
                            "analyzer": "modified_analyzer",
                        },
                        "abbreviation": {
                            "type": "text",
                            "analyzer": "modified_analyzer",
                        },
                        "journalIssueInformation": {
                            "type": "nested",
                            "properties": {
                                "medium": {"type": "keyword", "null_value": "NONE"},
                                "volume": {"type": "keyword", "null_value": "NONE"},
                                "issueNumber": {
                                    "type": "keyword",
                                    "null_value": "NONE",
                                },
                                "issueDate": {
                                    "type": "nested",
                                    "properties": {
                                        "year": {
                                            "type": "keyword",
                                            "null_value": "NONE",
                                        },
                                        "month": {
                                            "type": "keyword",
                                            "null_value": "NONE",
                                        },
                                        "day": {
                                            "type": "keyword",
                                            "null_value": "NONE",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                "keywords": {
                    "type": "nested",
                    "properties": {
                        "major": {"type": "keyword", "null_value": "NONE"},
                        "name": {"type": "text", "analyzer": "modified_analyzer"},
                    },
                },
                "language": {"type": "keyword", "null_value": "NONE"},
                "meshTerms": {
                    "type": "nested",
                    "properties": {
                        "major": {"type": "keyword", "null_value": "NONE"},
                        "meshID": {"type": "keyword", "null_value": "NONE"},
                        "name": {"type": "text", "analyzer": "modified_analyzer"},
                    },
                },
                "nlpProcessedFlag": {"type": "keyword", "null_value": "N"},
                "otherAbstract": {"type": "text", "analyzer": "modified_analyzer"},
                "publicationTypes": {
                    "type": "nested",
                    "properties": {
                        "publicationMeshID": {"type": "keyword", "null_value": "NONE"},
                        "publicationName": {"type": "keyword", "null_value": "NONE"},
                        "type": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            },
                        },
                    },
                },
                "status": {"type": "keyword", "null_value": "NONE"},
                "title": {"type": "text", "analyzer": "modified_analyzer"},
                "vectorisedFlag": {"type": "keyword", "null_value": "N"},
                "vernacularTitle": {"type": "text", "analyzer": "modified_analyzer"},
            }
        },
    }
    return os_mapping
