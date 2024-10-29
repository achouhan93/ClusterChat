from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import logging
import json
import utils
import os
from typing import List

from tasks.database import database_connection
from pipeline import Processor

# Load configuration
CONFIG = utils.loadConfigFromEnv()

# Setup logging
if not os.path.exists(CONFIG["CLUSTER_TALK_LOG_PATH"]):
    os.makedirs(CONFIG["CLUSTER_TALK_LOG_PATH"])

logging.basicConfig(
    filename=CONFIG["CLUSTER_TALK_LOG_EXE_PATH"],
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%m-%y %H:%M:%S",
    level=logging.INFO,
)


# Initialize the models and processor at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global processor
    # Database setup and indexing
    os_connection = database_connection.opensearch_connection()
    embedding_model = CONFIG["CLUSTER_TALK_EMBEDDING_MODEL"]
    embedding_index = CONFIG["CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_SENTENCE"]
    model_configs = json.loads(CONFIG["MODEL_CONFIGS"])

    # Initialize Processor
    processor = Processor(
        opensearch_connection=os_connection,
        embedding_os_index=embedding_index,
        embedding_model=embedding_model,
        model_config=model_configs["mixtral7B"],
    )
    yield
    os_connection.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    question_type: str  # 'corpus-based' or 'document-specific'
    supporting_information: List[str] = []


class AnswerResponse(BaseModel):
    answer: str
    sources: list


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    # Process the request
    try:
        if request.question_type not in ["corpus-specific", "document-specific"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid question_type. Must be 'corpus-specific' or 'document-specific'.",
            )

        # Use the processor to generate the answer
        if request.question_type == "corpus-specific":
            answer, sources = processor.process_corpus_specific_request(
                question=request.question,
                cluster_information=request.supporting_information
            )
        else:
            answer, sources = processor.process_api_request(
                question=request.question,
                document_ids=request.supporting_information,
            )

        return AnswerResponse(answer=answer, sources=sources)

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
