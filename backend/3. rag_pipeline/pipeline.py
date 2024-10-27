import logging
from datetime import datetime
from torch import cuda
from sentence_transformers import SentenceTransformer
import utils
import json
from tqdm import tqdm

# from langchain.retrievers.self_query.base import MetadataFieldInfo
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.retrievers import SelfQueryRetriever

# from langchain.chains import RetrievalQA
from langchain_openai import OpenAI

# from langchain.chains import LLMChain

from tasks.rag_components import rag_chatmodel, rag_loader, rag_prompt

log = logging.getLogger(__name__)
CONFIG = utils.loadConfigFromEnv()


class Processor:
    """
    Processor class to handle the text processing pipeline including text retrieval
    and generation using language models.
    """

    def __init__(
        self, opensearch_connection, embedding_os_index, embedding_model, model_config
    ):
        self.os_connection = opensearch_connection
        self.embeddings_os_index_name = embedding_os_index

        self.device = f"cuda:{cuda.current_device()}" if cuda.is_available() else "cpu"

        self.embed_model = SentenceTransformer(
            model_name_or_path=embedding_model,
            trust_remote_code=True,
            device=self.device,
        )

        self.scroll_size = 100

        self.vector_store = rag_loader.ragLoader().get_opensearch_index(
            self.embed_model, self.embeddings_os_index_name
        )

        self.model_config = model_config

        self.prompt = rag_prompt.ragPrompt().prompt_template()
        self.chat_model = rag_chatmodel.ragChat(
            self.vector_store,
            self.prompt,
            ["context", "question"],
            self.embed_model,
            self.model_config,
        )

        # Initialize SelfQueryRetriever for corpus-specific queries
        self.cluster_info_index = CONFIG["CLUSTER_TALK_CLUSTER_INFORMATION_INDEX"]
        # self.cluster_info_retriever = self.initialize_cluster_info_retriever()

    # def initialize_cluster_info_retriever(self):
    #     # Define metadata fields for the cluster information index
    #     metadata_field_info = [
    #         MetadataFieldInfo(
    #             name="cluster_id",
    #             description="The unique identifier for a cluster",
    #             type="string",
    #         ),
    #         MetadataFieldInfo(
    #             name="label",
    #             description="The name of the cluster representing a topic or theme",
    #             type="string",
    #         ),
    #         MetadataFieldInfo(
    #             name="depth",
    #             description="The depth level of the cluster in the hierarchy",
    #             type="integer",
    #         ),
    #         MetadataFieldInfo(
    #             name="is_leaf",
    #             description="Indicates if the cluster is a leaf node",
    #             type="boolean",
    #         ),
    #         MetadataFieldInfo(
    #             name="children",
    #             description="List of child cluster IDs",
    #             type="list[string]",
    #         ),
    #         MetadataFieldInfo(
    #             name="path",
    #             description="The hierarchical path of the cluster",
    #             type="string",
    #         ),
    #         MetadataFieldInfo(
    #             name="x",
    #             description="The x-coordinate of the node present in the cluster for visualization",
    #             type="float",
    #         ),
    #         MetadataFieldInfo(
    #             name="y",
    #             description="The y-coordinate of the node present in the cluster for visualization",
    #             type="float",
    #         ),
    #     ]

    #     # Create prompt template for SelfQueryRetriever
    #     field_descriptions = "\n".join(
    #         [f"- {field.name} ({field.type}): {field.description}" for field in metadata_field_info]
    #     )

    #     prompt_template = """
    #     You are an expert assistant helping to retrieve information from a clustered corpus of documents.

    #     Given a user's question, generate the best possible search query that filters documents based on the metadata fields provided.

    #     Available metadata fields:
    #     {field_descriptions}

    #     If the user mentions a cluster name, include it in your search query by matching it to the 'label' metadata field.

    #     User question:
    #     {query}

    #     Construct a search query using the metadata fields to retrieve relevant clusters or documents.
    #     """

    #     prompt = PromptTemplate(
    #         input_variables=["query"],
    #         template=prompt_template.format(field_descriptions=field_descriptions, query="{query}"),
    #     )

    #     # Initialize the language model for the retriever
    #     llm_retriever = ChatOpenAI(temperature=0)

    #     # Initialize vector store for the cluster information index
    #     cluster_info_vectorstore = rag_loader.ragLoader().get_opensearch_index(
    #         self.embed_model, self.cluster_info_index
    #     )

    #     # Create SelfQueryRetriever
    #     retriever = SelfQueryRetriever.from_llm(
    #         llm=llm_retriever,
    #         vectorstore=cluster_info_vectorstore,
    #         document_contents="Information about clusters including labels and hierarchy.",
    #         metadata_field_info=metadata_field_info,
    #         verbose=True,
    #         llm_chain_kwargs={'prompt': prompt}
    #     )

    #     return retriever

    def process_api_request(self, question, document_ids):
        """
        Process an API request to generate an answer based on the question, question type, and document IDs.

        :param question: The user's question as a string.
        :param question_type: Type of question, 'corpus-based' or 'document-specific'.
        :param document_ids: List of document IDs to restrict the search to. If empty, use the whole corpus.
        :return: A tuple (answer, sources)
        """
        try:
            context, retrieved_ids = self.chat_model.vector_augment_prompt_api(
                query=question, top_k_value=10, document_ids=document_ids
            )

            # Generate the answer
            answer = self.chat_model.llm_chain.invoke(
                {"context": context, "question": question}
            )
            cleaned_answer = answer.strip()
            return cleaned_answer, retrieved_ids

        except Exception as e:
            log.error(f"Error processing API request: {e}")
            raise RuntimeError(f"Error processing API request: {e}")

    # def process_corpus_specific_request(self, question):
    #     """
    #     Process a corpus-specific API request to generate an answer based on the question and corpus.

    #     :param question: The user's question as a string.
    #     :param corpus_specific: The corpus-specific string value.
    #     :return: A tuple (answer, sources)
    #     """
    #     try:
    #         # Use SelfQueryRetriever to retrieve relevant cluster information
    #         # TODO: Look into this part
    #         retrieved_docs = self.cluster_info_retriever.get_relevant_documents()

    #         # Aggregate retrieved information
    #         retrieved_info = "\n".join([doc.page_content for doc in retrieved_docs])

    #         # Generate the answer using LLM
    #         answer_prompt = f"""
    #         You are an expert assistant helping users explore a specific corpus.

    #         Given the user's question and the retrieved cluster information, provide a concise and informative answer.

    #         User Question:
    #         {question}

    #         Retrieved Information:
    #         {retrieved_info}

    #         Answer the question using the information above.
    #         """

    #         # Initialize LLM for answer generation
    #         llm_answer = OpenAI(temperature=0)

    #         # Create a prompt template
    #         answer_prompt_template = PromptTemplate(
    #             input_variables=["question", "retrieved_info"],
    #             template=answer_prompt
    #         )

    #         # Create LLMChain
    #         llm_chain = LLMChain(
    #             llm=llm_answer,
    #             prompt=answer_prompt_template,
    #         )

    #         # Generate the answer
    #         answer = llm_chain.run({
    #             "question": question,
    #             "retrieved_info": retrieved_info
    #         })

    #         cleaned_answer = answer.strip()

    #         # Extract source information (e.g., cluster IDs)
    #         sources = [doc.metadata.get("cluster_id") for doc in retrieved_docs]

    #         return cleaned_answer, sources

    #     except Exception as e:
    #         log.error(f"Error processing corpus-specific request: {e}")
    #         raise RuntimeError(f"Error processing corpus-specific request: {e}")
