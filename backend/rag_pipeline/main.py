import json
import logging
import os
from typing import List, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, field_validator

import utils
from tasks.database import database_connection
from pipeline import Processor

# Load configuration
CONFIG = utils.load_config_from_env()

# Setup logging
if not os.path.exists(CONFIG["CLUSTER_CHAT_LOG_PATH"]):
    os.makedirs(CONFIG["CLUSTER_CHAT_LOG_PATH"])

logging.basicConfig(
    filename=CONFIG["CLUSTER_CHAT_LOG_EXE_PATH"],
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%m-%y %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# Global processor instance
processor: Processor


# Initialize the models and processor at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for startup/shutdown tasks.

    Initializes the OpenSearch connection and the Processor instance.
    """
    global processor
    # Database setup and indexing
    os_connection = database_connection.opensearch_connection()
    embedding_model = CONFIG["CLUSTER_CHAT_EMBEDDING_MODEL"]
    embedding_index = CONFIG["CLUSTER_CHAT_OPENSEARCH_TARGET_INDEX_SENTENCE"]
    model_configs = json.loads(CONFIG["MODEL_CONFIGS"])

    # Initialize Processor
    processor = Processor(
        opensearch_connection=os_connection,
        embedding_os_index=embedding_index,
        embedding_model=embedding_model,
        model_config=model_configs["mixtral7B"],
    )
    log.info("Processor initialized and ready.")
    yield
    os_connection.close()
    log.info("OpenSearch connection closed.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    question_type: str  # 'corpus-based' or 'document-specific'
    supporting_information: List[Union[str, int]] = []

    @field_validator("supporting_information", mode='before')
    def convert_all_to_str(cls, v):
        return [str(item) for item in v]


class AnswerResponse(BaseModel):
    answer: str
    sources: list


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest) -> AnswerResponse:
    """
    Accepts a user question and routes it to the appropriate processor method
    depending on the question type.

    Returns:
        AnswerResponse: Answer text and a list of source document IDs.
    """
    try:
        if request.question_type not in ["corpus-specific", "document-specific"]:
            log.warning("Invalid question_type received: %s", request.question_type)
            raise HTTPException(
                status_code=400,
                detail="Invalid question_type. Must be 'corpus-specific' or 'document-specific'.",
            )

        # Use the processor to generate the answer
        if request.question_type == "corpus-specific":
            answer, sources = processor.process_corpus_specific_request(
                question=request.question,
                cluster_information=request.supporting_information,
            )
        else:
            answer, sources = processor.process_api_request(
                question=request.question,
                document_ids=request.supporting_information,
            )

        log.info("Successfully processed question.")
        return AnswerResponse(answer=answer, sources=sources)

    except Exception as e:
        log.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed")
async def get_embedding(request: Request):
    """
    Computes and returns the embedding for a given query.

    Request body should be: { "query": "your input text" }

    Returns:
        JSONResponse: { "embedding": [...] }
    """
    try:
        body = await request.json()
        query_text = body.get("query")

        if not query_text:
            log.warning("Missing 'query' in /embed request.")
            raise HTTPException(
                status_code=400, detail="Missing 'query' field in body."
            )

        embedding = processor.encode_text(query_text)
        log.info("Successfully generated embedding.")
        return JSONResponse(content={"embedding": embedding})

    except Exception as e:
        log.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding.")
