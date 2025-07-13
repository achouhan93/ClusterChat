<a name="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks](https://img.shields.io/github/forks/achouhan93/ClusterChat.svg?style=for-the-badge)](https://github.com/achouhan93/ClusterChat/forks)
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
![Visitors](https://api.visitorbadge.io/api/VisitorHit?user=achouhan93&repo=ClusterChat&countColor=%237B1E7A)

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/achouhan93/ClusterChat">
    <img src="images/exploration.png" alt="Logo" width="80" height="80">
  </a>
  <h3 align="center">ClusterChat: A Multi-Feature Search for Corpus Exploration</h3>
  
  <p align="center">
  Ashish Chouhan, Saifeldin Mandour, and Michael Gertz 
  
  Heidelberg University
  
  Contact us at: [`{chouhan, gertz}@informatik.uni-heidelberg.de`](mailto:chouhan@informatik.uni-heidelberg.de), [`saifeldin.mandour@stud.uni-heidelberg.de`](mailto:saifeldin.mandour@stud.uni-heidelberg.de)
  
  <a href="https://github.com/achouhan93/ClusterChat/issues">Report Bug</a> · <a href="https://github.com/achouhan93/ClusterChat/issues">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
      <li>
        <a href="#about-the-project">About The Project</a>
        <ul>
          <li><a href="#abstract">Abstract</a></li>
        </ul>
      </li>
      <li>
        <a href="#project-structure">Project Structure</a>
        <ul>
          <li><a href="#backend">Backend</a></li>
        </ul>
        <ul>
          <li><a href="#frontend">Frontend</a></li>
        </ul>
      </li>
      <li><a href="#getting-started">Getting Started</a></li>
        <ul>
        <li><a href="#setting-up-backend">Setting up Backend</a></li>
        <li><a href="#setting-up-frontend">Setting up Frontend</a></li>
        </ul>
    </li>
    <li><a href="#cite-our-work">Cite our work</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

Video demonstration: [here](https://youtu.be/NxxkWOhIRzw)

### Abstract
Exploring large-scale text corpora presents a significant challenge in biomedical, finance, and legal domains, where vast amounts of documents are continuously published. Traditional search methods, such as keyword-based search, often retrieve documents in isolation, limiting the user's ability to easily inspect corpus-wide trends and relationships. We present $\textit{ClusterChat}$ (The demo video and source code are available at: https://github.com/achouhan93/ClusterChat), an open-source system for corpus exploration that integrates cluster-based organization of documents using textual embeddings with lexical and semantic search, timeline-driven exploration, and corpus and document-level question answering (QA) as multi-feature search capabilities. We validate the system with two case studies on a four million abstract PubMed dataset, demonstrating that $\textit{ClusterChat}$ enhances corpus exploration by delivering context-aware insights while maintaining scalability and responsiveness on large-scale document collections.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

The $\textit{ClusterChat}$ framework provides a web-based tool for exploring [PubMed abstracts](https://pubmed.ncbi.nlm.nih.gov/), utilizing backend components for document clustering and retrieval-augmented generation (RAG). It employs [BERTopic](https://maartengr.github.io/BERTopic/index.html) and [LangChain](https://www.langchain.com/) for the backend processing, with [Cosmograph](https://cosmograph.app/) used for interactive visualizations in the frontend. This setup supports both multi-feature search on abstracts and natural language query capabilities for enhanced corpus navigation.

### Backend

**Folder:** `backend/`

1. **Data Collection and Storage** (`1.embedding_data_storage`): PubMed abstracts from 2020–2024 were collected and stored in OpenSearch, yielding about four million abstracts with metadata.

2. **Topic Modeling and Clustering Information** (`2.topic_modelling` and `3. cluster_information`): Abstracts are embedded with [NeuML/pubmedbert-base-embeddings](https://huggingface.co/NeuML/pubmedbert-base-embeddings), reduced in dimensionality via UMAP, and clustered using HDBSCAN. Keywords and labels for each cluster are generated using BM25 and GPT-4o-mini, and stored in OpenSearch.

3. **RAG Pipeline** (`rag_pipeline`): For question answering, abstracts are segmented into sentences, creating around $46$ million sentence embeddings indexed in OpenSearch. Document-level queries retrieve contextually relevant sentence chunks, which are then processed with [Mixtral-8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) or OpenAI to generate precise answers with citations pointing to respective PubMed Abstract.

### Frontend

![Figure 1: Overview of the ClusterChat interface][clusterchat_interface] <p align="center">_Figure 1: Overview of the web-based $\textit{ClusterChat}$ interface. The interface includes four main features: 1) a chat panel on the top-left for corpus and document-level question answering; 2) a metadata information panel on the bottom-left for displaying metadata information of the selected documents; 3) a central cluster visualization map showing research topics like ''Cancer Treatment'' and ''Genetic Disorders''; 4) a search panel at the top to perform a lexical and semantic search on ''Abstract'' text and a keyword search on ''Title'' text._</p>

**Folder:** `app/`

1. **Cluster Overview:** Visualizes thematic clusters, like “Cancer Treatment,” and allows for intuitive exploration.

2. **Search and Filtering:** Filters documents by date, keywords, semantics, and clusters, refining corpus exploration.

3. **Question-Answering Interface:** Supports document-level and corpus-level queries, allowing users to ask both targeted and broad questions about selected clusters or the entire corpus.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Clone the repository by executing the below command
  ```sh
  git clone https://github.com/achouhan93/ClusterChat.git
  ```

Navigate to the cloned repository folder
  ```sh
  cd ClusterChat
  ```

Once the repository is successfully cloned and user navigated to the folder.

### Setting up Backend
Execute the below steps to setup Python Environment (tested with Python 3.9.0):
  1. Setup a venv with python (or `conda`)

  ```sh
  python -m venv .venv
  ```

2. Activate venv

  ```sh
  source .venv/bin/activate
  ```

3. Install all necessary dependencies by running

  ```sh
  pip install -r requirements.txt
  ```

4. Rename the `.env-example` to `.env` and populate the file with the required credentials

```sh
CLUSTER_CHAT_LOG_EXE_PATH="logs/insights_execution.log"
CLUSTER_CHAT_LOG_PATH="logs/"

# Required for Backend functionalities, i.e., Embedding creation and storage, 
# Topic Modeling and Clustering information construction and storage,
# Retrieval Augmented Generation (RAG) or QA Pipeline to work

# Opensearch Connection Details
OPENSEARCH_USERNAME = "your_opensearch_username"
OPENSEARCH_PASSWORD = "your_opensearch_password"
OPENSEARCH_PORT=your_opensearch_port
CLUSTER_CHAT_OPENSEARCH_HOST="your_opensearch_host_name"

CLUSTER_CHAT_OPENSEARCH_SOURCE_INDEX="frameintell_pubmed"
CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_COMPLETE="frameintell_pubmed_abstract_embeddings"
CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_SENTENCE="frameintell_pubmed_sentence_embeddings"
CLUSTER_CHAT_CLUSTER_INFORMATION_INDEX="frameintell_clusterchat_clusterinformation"
CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX="frameintell_clusterchat_documentinformation"

# HuggingFace Key
HUGGINGFACE_AUTH_KEY = "your-huggingface-api-key"

## Required for embedding computation for Abstract and Sentences
CLUSTER_CHAT_EMBEDDING_MODEL="NeuML/pubmedbert-base-embeddings"
## Required for topic label and topic description generation
OPENAI_API_KEY = "your-openapi-key"
## Required for Answer Generation in the QA Pipeline
MODEL_CONFIGS = '{"mixtral7B": {"temperature": 0.3, "max_tokens": 100, "huggingface_model":"mistralai/Mixtral-8x7B-Instruct-v0.1", "repetition_penalty":1.2, "stop_sequences":["<|endoftext|>", "</s>"]}}'

# For storage of the BERTopic models at the intermediate stage
MODEL_PATH = "./intermediate_results/"

# Required for frontend
APP_URL="http://localhost:5173"
OPENSEARCH_NODE="https://your-opensearch-hostname:your-opensearch-port"
```

5. Start the backend server:
   ```sh
   cd backend/rag_pipeline
   uvicorn main:app --reload --port 8100
   ```

### Setting up Frontend
Execute the below steps to setup frontend:

1. Navigate to the app folder:
   ```sh
   cd app
   ```

2. Install frontend dependencies:
   ```sh
   npm install
   ```

3. Start the frontend server:
   ```sh
   npm run dev
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ## Usage

- **Embedding Data Storage**: Converts PubMed abstracts into embeddings using `--chunking` options for sentence or full-abstract level.
- **Topic Modeling**: Generates BERTopic models in federated learning intervals, using UMAP and HDBSCAN.
- **RAG Pipeline**: Allows question answering based on document- or corpus-level queries. Document-specific answers use metadata-enhanced vector search, while corpus-specific queries analyze clusters and intents.
- **Cluster Information**: Consolidates topics from different BERTopic models, creating a hierarchical topic structure stored in OpenSearch.

<p align="right">(<a href="#readme-top">back to top</a>)</p> -->

## Cite our work

No current information

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License
We use the standard [MIT](https://choosealicense.com/licenses/mit/) license for code artifacts.
See `license/LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments
We thank the Bundesministerium für Bildung und Forschung
(BMBF) for funding this research within the [FrameIntell project](https://frameintell.de/).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/achouhan93/ClusterChat.svg?style=for-the-badge
[contributors-url]: https://github.com/achouhan93/ClusterChat/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/achouhan93/ClusterChat.svg?style=for-the-badge
[forks-url]: https://github.com/achouhan93/ClusterChat/forks
[stars-shield]: https://img.shields.io/github/stars/achouhan93/ClusterChat.svg?style=for-the-badge
[stars-url]: https://github.com/achouhan93/ClusterChat/stargazers
[issues-shield]: https://img.shields.io/github/issues/achouhan93/ClusterChat.svg?style=for-the-badge
[issues-url]: https://github.com/achouhan93/ClusterChat/issues
[license-shield]: https://img.shields.io/github/license/achouhan93/ClusterChat.svg?style=for-the-badge
[license-url]: https://github.com/achouhan93/ClusterChat/blob/main/LICENSE
[clusterchat_interface]: images/clusterchat.png