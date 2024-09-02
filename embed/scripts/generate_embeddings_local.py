from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import numpy as np
import json

# Variables
model = "Alibaba-NLP/gte-large-en-v1.5"
device = "cuda"
read_path = "data/cleaned_texts_for_embedding.json"
write_path = "data/embeddings.npz"
batch_size = 100000  # Adjust based on memory constraints


# Function to prepare text for embedding
def prepare_text(paper):
    return (
        paper.get("title", "")
        + " "
        + paper.get("abstract", "")
        + " "
        + paper.get("journal-ref", "")
        + " "
        + paper.get("categories", "")
    ).strip()


# Function to encode a batch of texts
def encode_batch(batch):
    return model.encode(batch, show_progress_bar=True)


# Read the cleaned abstracts
with open(read_path, "r") as file:
    papers = [json.loads(line) for line in file]

# Prepare texts and ids
texts = [prepare_text(paper) for paper in papers]
ids = [paper["id"] for paper in papers]

# Load the model
model = SentenceTransformer(model, device=device, trust_remote_code=True)

# Generate embeddings
embeddings = []
for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
    batch = texts[i : i + batch_size]
    batch_embeddings = encode_batch(batch)
    embeddings.extend(batch_embeddings)

# Convert to numpy arrays
ids_array = np.array(ids)
embeddings_array = np.array(embeddings)

# Save the embeddings and ids
np.savez(
    write_path,
    ids=ids_array,
    embeddings=embeddings_array,
)
print(f"Embeddings generated and saved to '{write_path}'.")
