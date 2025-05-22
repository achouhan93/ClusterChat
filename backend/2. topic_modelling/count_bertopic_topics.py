import os
import pickle
from bertopic import BERTopic
import gc

def list_bertopic_models(model_dir, prefix="bertopic_model_", suffix=".pkl"):
    return [
        os.path.join(model_dir, file)
        for file in os.listdir(model_dir)
        if file.startswith(prefix) and file.endswith(suffix)
    ]

def count_topics_in_models(model_dir):
    model_paths = list_bertopic_models(model_dir)
    print(f"Found {len(model_paths)} BERTopic model(s).")

    total_topics = 0

    for idx, model_path in enumerate(model_paths, start=1):
        print(f"\n[{idx}/{len(model_paths)}] Processing: {os.path.basename(model_path)}")
        try:
            model = BERTopic.load(model_path)
            topics = model.get_topics()
            num_topics = len([tid for tid in topics if tid != -1])  # Exclude outlier topic -1
            print(f"Number of valid topics: {num_topics}")
            total_topics += num_topics
        except Exception as e:
            print(f"Failed to process {model_path}: {e}")
        finally:
            # Explicitly delete model and clean up memory
            del model
            gc.collect()

    print(f"\n✅ Total number of topics across all models: {total_topics}")

if __name__ == "__main__":
    model_directory = "../../intermediate_results"  # <- Update this path
    count_topics_in_models(model_directory)