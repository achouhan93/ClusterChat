def opensearch_create(os_connection, index_name, os_mapping):
    # """"""""""
    # Functionality: Creation of the Index if not present in the cluster
    #
    # Signature of the function:
    #  Input:
    #       os_connection: OpenSearch connection
    #       index_name: Name of the index that needs to be created
    #       os_mapping: Mapping of the index that needs to be created
    #
    #  Output:
    #       If the index is already present then the function wont take any action
    #       And if the index is not present then it will be created by the function
    # """"""""""
    search_index = os_connection.indices.exists(index=index_name)

    if search_index == False:
        os_connection.indices.create(
            index=index_name, ignore=[400, 404], body=os_mapping
        )
