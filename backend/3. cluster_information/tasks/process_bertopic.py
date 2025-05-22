import os
import gc
import json
import numpy as np
import logging
from bertopic import BERTopic
from openai import OpenAI
import pickle
from utils import load_config_from_env
from time import sleep

log = logging.getLogger(__name__)
CONFIG = load_config_from_env()

# Initialize OpenAI client
client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def list_bertopic_models(model_path):
    """Lists all BERTopic models stored in the given path."""
    model_files = []
    for root, _, files in os.walk(model_path):
        for file in files:
            if file.startswith("bertopic_model_") and file.endswith(".pkl"):
                model_files.append(os.path.join(root, file))
    return model_files


# def get_topic_label(topic_words):
#     prompt = f"Provide a concise and informative label of two words for a topic represented by the following words, listed in order of importance: {', '.join([word for word, _ in topic_words])}. The earlier words are more important."
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",  # Or another suitable model like 'gpt-3.5-turbo'
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a helpful assistant that generates concise topic labels of two words. Prioritize earlier words as they are more important when creating the label.",
#             },
#             {"role": "user", "content": prompt},
#         ],
#         max_tokens=10,
#         n=1,
#         temperature=0.1,
#     )
#     label = response.choices[0].message.content.strip()  # Access content from message
#     return label


# def get_topic_description(topic_words):
#     prompt = f"Provide a brief, informative description for a topic represented by the following words, listed in order of importance: {', '.join([word for word, _ in topic_words])}. Earlier words are more important and should be emphasized in the description."

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a helpful assistant that generates concise and informative topic descriptions. Use the words provided, emphasizing the most important ones that appear first.",
#             },
#             {"role": "user", "content": prompt},
#         ],
#         max_tokens=20,
#         n=1,
#         temperature=0.5,
#     )
#     description = response.choices[0].message.content.strip()
#     return description

def get_topic_metadata(topic_words):
    prompt = (
        f"You are given topic keywords in order of importance: {', '.join([word for word, _ in topic_words])}. "
        f"Generate a JSON object with the following two fields:\n"
        f"- 'label': A concise topic label using **at most three words**, summarizing the topic clearly. Do not use punctuation.\n"
        f"- 'description': A short informative sentence of **at most 15 words** that summarizes the topic, emphasizing the most important terms.\n\n"
        f"Return only a valid JSON object and nothing else."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that returns structured JSON data for topic modeling.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=50,
        temperature=0.1,
    )

    content = response.choices[0].message.content.strip()
    try:
        metadata = json.loads(content)
    except Exception as e:
        metadata = {
            "label": None,
            "description": None,
            "error": f"Failed to parse JSON: {e}",
            "raw_output": content
        }
    return metadata

def save_checkpoint(checkpoint_path, checkpoint_data):
    """Saves the current checkpoint data to a file."""
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_data, f)
    log.info(f"Checkpoint saved at {checkpoint_path}.")


def load_checkpoint(checkpoint_path):
    """Loads checkpoint data from a file."""
    with open(checkpoint_path, "rb") as f:
        checkpoint_data = pickle.load(f)
    log.info(f"Checkpoint loaded from {checkpoint_path}.")
    return checkpoint_data


def process_models(model_path):
    checkpoint_path = os.path.join(model_path, "checkpoint.pkl")
    log.info("Starting the processing of the BERTopic Model")
    # Initialize or load checkpoint
    if os.path.exists(checkpoint_path):
        checkpoint = load_checkpoint(checkpoint_path)
        merged_topics = checkpoint["merged_topics"]
        merged_topic_embeddings = checkpoint["merged_topic_embeddings"]
        topic_id_to_index = checkpoint["topic_id_to_index"]
        current_topic_id = checkpoint["current_topic_id"]
        topic_label = checkpoint["topic_label"]
        topic_description = checkpoint["topic_description"]
        topic_words = checkpoint["topic_words"]
        processed_models = checkpoint["processed_models"]
    else:
        # Initialize variables
        merged_topics = {}
        merged_topic_embeddings = []
        topic_id_to_index = {}
        current_topic_id = 0
        topic_label = {}
        topic_description = {}
        topic_words = {}
        processed_models = []

    # List all BERTopic models
    model_paths = list_bertopic_models(model_path)
    log.info(f"Found {len(model_paths)} BERTopic model(s) in {model_path}.")

    # Filter out already processed models
    models_to_process = [m for m in model_paths if m not in processed_models]
    log.info(f"{len(models_to_process)} model(s) left to process.")

    # Process models one at a time to minimize memory usage
    for model_num, path in enumerate(models_to_process, start=1):
        try:
            log.info(
                f"Processing Started for model {model_num + 1}/{len(model_paths)}: {path}"
            )

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
            sleep(2)

            # Update the merged topics and embeddings for the next iteration
            merged_topics = all_topics
            merged_topic_embeddings = all_topic_embeddings
            topic_id_to_index = all_topic_id_to_index

            # Generate topic descriptions for new topics
            for tid in batch_topics.keys():
                words = batch_topics[tid]
                topic_words[tid] = [word for word, _ in words]
                metadata = get_topic_metadata(words)
                # topic_label[tid] = get_topic_label(words)
                topic_label[tid] = metadata.get("label")
                topic_description[tid] = metadata.get("description")
                # topic_description[tid] = get_topic_description(words)
                sleep(2)

            # Clean up variables to free memory
            del batch_topics
            del batch_topic_embeddings
            del batch_topic_id_to_index
            gc.collect()
            sleep(2)

            # Update processed models
            processed_models.append(path)

            # Save checkpoint after processing each model
            checkpoint_data = {
                "merged_topics": merged_topics,
                "merged_topic_embeddings": merged_topic_embeddings,
                "topic_id_to_index": topic_id_to_index,
                "current_topic_id": current_topic_id,
                "topic_label": topic_label,
                "topic_description": topic_description,
                "topic_words": topic_words,
                "processed_models": processed_models,
            }

            save_checkpoint(checkpoint_path, checkpoint_data)

            log.info(
                f"Processing Completed for model {model_num + 1}/{len(model_paths)}: {path}"
            )
        except Exception as e:
            log.error(f"Error processing model {path}: {e}")
            log.error("Saving checkpoint before exiting.")
            # Save the current state before exiting
            checkpoint_data = {
                "merged_topics": merged_topics,
                "merged_topic_embeddings": merged_topic_embeddings,
                "topic_id_to_index": topic_id_to_index,
                "current_topic_id": current_topic_id,
                "topic_label": topic_label,
                "topic_description": topic_description,
                "topic_words": topic_words,
                "processed_models": processed_models,
            }
            save_checkpoint(checkpoint_path, checkpoint_data)
            log.info("Exiting the script due to errors.")
            raise  # Re-raise the exception after saving checkpoint

    log.info(
        "Processing for all models completed and topics are merged with topic information"
    )

    # Save the final merged_topic_embeddings_array
    merged_topic_embeddings_array = np.array(merged_topic_embeddings, dtype=np.float32)
    final_npy_path = os.path.join(model_path, "merged_topic_embeddings_array.npy")
    np.save(final_npy_path, merged_topic_embeddings_array)
    log.info(f"Final merged_topic_embeddings_array.npy saved at {final_npy_path}.")

    # Optionally, save other merged data for future use
    with open(os.path.join(model_path, "merged_topics.pkl"), "wb") as f:
        pickle.dump(merged_topics, f)
    with open(os.path.join(model_path, "topic_label.pkl"), "wb") as f:
        pickle.dump(topic_label, f)
    with open(os.path.join(model_path, "topic_description.pkl"), "wb") as f:
        pickle.dump(topic_description, f)
    with open(os.path.join(model_path, "topic_words.pkl"), "wb") as f:
        pickle.dump(topic_words, f)
    log.info("All merged topic information saved as pickle files.")

    # Optionally, remove the checkpoint file as processing is complete
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        log.info(
            f"Checkpoint file {checkpoint_path} removed after successful processing."
        )

    return (
        merged_topics,
        merged_topic_embeddings_array,
        topic_label,
        topic_description,
        topic_words,
    )
