import os
import gc
import numpy as np
import logging
from bertopic import BERTopic
from openai import OpenAI
import logging
from utils import load_config_from_env

log = logging.getLogger(__name__)
CONFIG = load_config_from_env()

# Initialize OpenAI client
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

# Initialize logging
logging.basicConfig(level=logging.INFO)


def list_bertopic_models(model_path):
    """Lists all BERTopic models stored in the given path."""
    model_files = []
    for root, _, files in os.walk(model_path):
        for file in files:
            if file.startswith("bertopic_model_") and file.endswith(".pkl"):
                model_files.append(os.path.join(root, file))
    return model_files


def get_topic_label(topic_words):
    prompt = f"Provide a concise and informative label of two words for a topic represented by the following words, listed in order of importance: {', '.join([word for word, _ in topic_words])}. The earlier words are more important."
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Or another suitable model like 'gpt-3.5-turbo'
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates concise topic labels of two words. Prioritize earlier words as they are more important when creating the label.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=10,
        n=1,
        temperature=0.1,
    )
    label = response.choices[0].message.content.strip()  # Access content from message
    return label


def get_topic_description(topic_words):
    prompt = f"Provide a brief, informative description for a topic represented by the following words, listed in order of importance: {', '.join([word for word, _ in topic_words])}. Earlier words are more important and should be emphasized in the description."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates concise and informative topic descriptions. Use the words provided, emphasizing the most important ones that appear first.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=20,
        n=1,
        temperature=0.5,
    )
    description = response.choices[0].message.content.strip()
    return description


def process_models(model_path):
    
    logging.info("Starting the processing of the BERTopic Model")
    # Initialize variables to hold the merged topics and embeddings
    merged_topics = {}
    merged_topic_embeddings = []
    topic_id_to_index = {}
    current_topic_id = 0
    topic_label = {}
    topic_description = {}
    topic_words = {}

    # List all BERTopic models
    model_paths = list_bertopic_models(model_path)

    # Process models one at a time to minimize memory usage
    for model_num, path in enumerate(model_paths):
        logging.info(f"Processing Started for model {model_num + 1}/{len(model_paths)}: {path}")

        # Load the model
        model = BERTopic.load(path)

        # Extract topics and embeddings from the model
        topics = model.get_topics()
        embeddings = model.topic_embeddings_
        topic_keys = list(topics.keys())

        batch_topics = {}
        batch_topic_embeddings = []
        batch_topic_id_to_index = {}

        for i, topic_id in enumerate(topic_keys):
            if topic_id == -1:
                continue  # Skip outlier topic
            # Assign a new topic ID
            new_topic_id = current_topic_id
            current_topic_id += 1
            batch_topics[new_topic_id] = topics[topic_id]
            batch_topic_id_to_index[new_topic_id] = len(batch_topic_embeddings)
            batch_topic_embeddings.append(embeddings[i])

        # Combine existing merged topics with batch topics
        all_topics = {**merged_topics, **batch_topics}
        all_topic_embeddings = merged_topic_embeddings + batch_topic_embeddings
        all_topic_id_to_index = {**topic_id_to_index, **batch_topic_id_to_index}

        # Free memory from the loaded model
        del model
        gc.collect()

        # Update the merged topics and embeddings for the next iteration
        merged_topics = all_topics
        merged_topic_embeddings = all_topic_embeddings
        topic_id_to_index = all_topic_id_to_index

        # Generate topic descriptions for new topics
        for tid in batch_topics.keys():
            words = batch_topics[tid]
            topic_words[tid] = [word for word, _ in words]
            topic_label[tid] = get_topic_label(words)
            topic_description[tid] = get_topic_description(words)

        # Clean up variables to free memory
        del batch_topics
        del batch_topic_embeddings
        del batch_topic_id_to_index
        gc.collect()

        logging.info(f"Processing Completed for model {model_num + 1}/{len(model_paths)}: {path}")

    logging.info("Processing for all models completed and topics are merged with topic information")

    return (
        merged_topics,
        merged_topic_embeddings,
        topic_label,
        topic_description,
        topic_words,
    )
