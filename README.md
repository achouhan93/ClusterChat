<a name="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks](https://img.shields.io/github/forks/achouhan93/ClusterTalk.svg?style=for-the-badge)](https://github.com/achouhan93/ClusterTalk/forks)
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/achouhan93/ClusterTalk">
    <img src="images/exploration.png" alt="Logo" width="80" height="80">
  </a>
  <h3 align="center">ClusterTalk: Corpus Exploration Framework using Multi-Dimensional Exploratory Search</h3>
  
  <p align="center">
  Ashish Chouhan, Saifeldin Mandour, and Michael Gertz 
  
  Heidelberg University
  
  Contact us at: [`{chouhan, gertz}@informatik.uni-heidelberg.de`](mailto:chouhan@informatik.uni-heidelberg.de), [`saifeldin.mandour@stud.uni-heidelberg.de`](mailto:saifeldin.mandour@stud.uni-heidelberg.de)
  
  <a href="https://github.com/achouhan93/ClusterTalk/issues">Report Bug</a> · <a href="https://github.com/achouhan93/ClusterTalk/issues">Request Feature</a>
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

Video demonstration: [here](https://youtu.be/CRaus2J9mF8)

### Abstract
Exploratory search of large text corpora is essential in domains like biomedical research, where large amounts of research literature are continuously generated. This paper presents $\textit{ClusterTalk}$ (The demo video and source code are available at: https://github.com/achouhan93/ClusterTalk), a framework for corpus exploration using multi-dimensional exploratory search. Our system integrates document clustering with faceted search, allowing users to interactively refine their exploration and ask corpus and document-level queries. Compared to traditional one-dimensional search approaches like keyword search or clustering, this system improves the discoverability of information by encouraging a deeper interaction with the corpus. We demonstrate the functionality of the $\textit{ClusterTalk}$ framework based on four million PubMed abstracts for the four-year time frame.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

The $\textit{ClusterTalk}$ framework provides a web-based tool for exploring [PubMed abstracts](https://pubmed.ncbi.nlm.nih.gov/), utilizing backend components for document clustering and retrieval-augmented generation (RAG). It employs [BERTopic](https://maartengr.github.io/BERTopic/index.html) and [LangChain](https://www.langchain.com/) for backend processing, with [Cosmograph](https://cosmograph.app/) used for interactive visualizations in the frontend. This setup supports both faceted search on abstracts and natural language query capabilities for enhanced corpus navigation.

### Backend

**Folder:** `backend/`

1. **Data Collection and Storage** (`1.embedding_data_storage`): PubMed abstracts from 2020–2024 were collected and stored in OpenSearch, yielding about four million abstracts with metadata.

2. **Topic Modeling and Clustering Information** (`2.topic_modelling` and `4. cluster_information`): Abstracts are embedded with [NeuML/pubmedbert-base-embeddings](https://huggingface.co/NeuML/pubmedbert-base-embeddings), reduced in dimensionality via UMAP, and clustered using HDBSCAN. Keywords and labels for each cluster are generated using BM25 and GPT-4o-mini, and stored in OpenSearch.

3. **RAG Pipeline** (`3.rag_pipeline`): For question answering, abstracts are segmented into sentences, creating around $46$ million sentence embeddings indexed in OpenSearch. Document-level queries retrieve contextually relevant sentence chunks, which are then processed with [Mixtral-8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1) to generate precise answers with citations pointing to respective PubMed Abstract.

### Frontend

![Figure 1: Overview of the ClusterTalk interface][clustertalk_interface] <p align="center">_Figure 1: Overview of the ClusterTalk interface. The interface includes four main features: 1) a chat functionality panel on the top-left for asking corpus and document-level queries; 2) a metadata information panel on the bottom-left for displaying metadata information of the selected documents; 3) a central cluster visualization map showing research topics like “Cancer Treatment” and “Genetic Disorders”; 4) a faceted search panel at top for keyword search on `Title` and `Abstract` text._</p>

**Folder:** `app/`

1. **Cluster Overview:** Visualizes thematic clusters, like “Cancer Treatment,” and allows for intuitive exploration.

2. **Faceted Search and Filtering:** Filters documents by date, keywords, and clusters, refining corpus exploration.

3. **Question-Answering Interface:** Supports document-level and corpus-level queries, allowing users to ask both targeted and broad questions about selected clusters or the entire corpus.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Clone the repository by executing the below command
  ```sh
  git clone https://github.com/achouhan93/ClusterTalk.git
  ```

Navigate to the cloned repository folder
  ```sh
  cd ClusterTalk
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
CLUSTER_TALK_LOG_EXE_PATH="logs/insights_execution.log"
CLUSTER_TALK_LOG_PATH="logs/"

# Required for Backend functionalities, i.e., Embedding creation and storage, 
# Topic Modeling and Clustering information construction and storage,
# Retrieval Augmented Generation (RAG) or QA Pipeline to work

# Opensearch Connection Details
OPENSEARCH_USERNAME = "your_opensearch_username"
OPENSEARCH_PASSWORD = "your_opensearch_password"
OPENSEARCH_PORT=your_opensearch_port
CLUSTER_TALK_OPENSEARCH_HOST="your_opensearch_host_name"

CLUSTER_TALK_OPENSEARCH_SOURCE_INDEX="frameintell_pubmed"
CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_COMPLETE="frameintell_pubmed_abstract_embeddings"
CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_SENTENCE="frameintell_pubmed_sentence_embeddings"
CLUSTER_TALK_CLUSTER_INFORMATION_INDEX="frameintell_clustertalk_clusterinformation"
CLUSTER_TALK_DOCUMENT_INFORMATION_INDEX="frameintell_clustertalk_documentinformation"

# HuggingFace Key
HUGGINGFACE_AUTH_KEY = "your-huggingface-api-key"

## Required for embedding computation for Abstract and Sentences
CLUSTER_TALK_EMBEDDING_MODEL="NeuML/pubmedbert-base-embeddings"
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
   cd backend/3.\ rag_pipeline
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
[contributors-shield]: https://img.shields.io/github/contributors/achouhan93/ClusterTalk.svg?style=for-the-badge
[contributors-url]: https://github.com/achouhan93/ClusterTalk/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/achouhan93/ClusterTalk.svg?style=for-the-badge
[forks-url]: https://github.com/achouhan93/ClusterTalk/forks
[stars-shield]: https://img.shields.io/github/stars/achouhan93/ClusterTalk.svg?style=for-the-badge
[stars-url]: https://github.com/achouhan93/ClusterTalk/stargazers
[issues-shield]: https://img.shields.io/github/issues/achouhan93/ClusterTalk.svg?style=for-the-badge
[issues-url]: https://github.com/achouhan93/ClusterTalk/issues
[license-shield]: https://img.shields.io/github/license/achouhan93/ClusterTalk.svg?style=for-the-badge
[license-url]: https://github.com/achouhan93/ClusterTalk/blob/master/LICENSE
[clustertalk_interface]: images/clustertalkinterface.jpg
