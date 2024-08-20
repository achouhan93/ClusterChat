# 2024-ECIR-Corpus-Explorer

## Target conference information
ECIR Demo Paper: https://ecir2025.eu/call-for-demo-papers/
Submission Date: 23rd October 2024
Notificatioin Date: 16th December 2024
Conference: 6th-10th April 2025

## Related Softwares and Applications
- PubMed Landscape:
    - PubMed Landscape Application: https://static.nomic.ai/pubmed.html
    - PubMed Landscape Github: https://github.com/berenslab/pubmed-landscape
- Carrot2: https://search.carrot2.org
- SciSpace Application: https://typeset.io

## Reference Project and Application
- Reference: https://git-dbs.ifi.uni-heidelberg.de/practicals/2024-arjan-sujit-siddhpura
- Cosmograph 
    - Cosmograph: https://cosmograph.app/examples
    - Cosmograph Example: https://cosmograph.app/run/?embedding=https://cosmograph.app/data/arxiv_papers_100K.csv&nodeColor=color-cluster

## :fire: Points to Remember while building application:
- [ ] Latency is an essential factor during the display of cluster and while interacting with the application
- [ ] Time required to get answer and play-around with the application MUST be as low as possible
- [ ] Security, i.e., credentials must not be exposed in the application to interact with OpenSearch or with any database
- [ ] Application Stack: 
    - Database: OpenSearch
    - Programming Language:
        - Backend: Python (FastAPI or direct integration)
        - Frontend: Svelte-kit and Cosmograph

## :bangbang: Replicate the features from the existing features present in the Practical Project:
- [ ] Zooming in and zooming out in the cluster
- [ ] Showing some labels in the default setting and, when zoomed in then, showing more labels of the node in the region that is zoomed in
- [ ] Showing labels on hover
- [ ] Lexical Search on Title and Description/Abstract
- [ ] When one paper is selected, one can ask questions and get answers.
- [ ] Activating and deactivating the clusters
- [ ] Selecting documents based on time range (present at the bottom) and showing selected papers

## :bulb: Below are the features that the application must comprise of :bulb:
- [ ] Show labels for clusters displayed on the screen (Abstract labels, Hierarchical labels, and detailed labels)
- [ ] If a cluster is selected, one can perform question-answering on that cluster.
- [ ] If a particular section is selected, one can ask questions about that section.
- [ ] How to tackle questions like What is this cluster about? Provide topics present in this cluster.
- [ ] Provide questions that one can ask for the respective selected cluster.
- [ ] :thinking: How can we make it more intuitive?
- [ ] Chatbot at the side to interact with the cluster

## :bulb: Brainstorming Points
- [ ] Self-Querying LangChain: https://python.langchain.com/v0.1/docs/modules/data_connection/retrievers/self_query/
    - Based on the metadata information get information from the user query, if there is no output or there are multiple values for the value then query is not sufficient and more information is required as an input. This is the follow-up question for the user
- [ ] Try to integrate as much functionality from the OpenResearcher Paper - https://arxiv.org/pdf/2408.06941
    - Citation