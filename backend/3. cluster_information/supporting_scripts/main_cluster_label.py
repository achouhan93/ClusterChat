import json
import logging
from typing import List, Dict, Any, Optional

from opensearchpy import OpenSearch
from openai import OpenAI

import utils

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment-based configuration
CONFIG = utils.load_config_from_env()
INDEX_NAME = "frameintell_clusterchat_clusterinformation"
openai_client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])


def opensearch_connection() -> OpenSearch:
    """
    Establishes a secure connection to an OpenSearch cluster.

    Returns:
        OpenSearch: An authenticated OpenSearch client instance.
    """
    try:
        username: str = CONFIG["OPENSEARCH_USERNAME"]
        password: str = CONFIG["OPENSEARCH_PASSWORD"]
        host: str = CONFIG["CLUSTER_CHAT_OPENSEARCH_HOST"]
        port: int = int(CONFIG["OPENSEARCH_PORT"])

        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(username, password),
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

        logger.info("OpenSearch connection established.")
        return client

    except KeyError as ke:
        logger.error(f"Missing configuration key: {str(ke)}")
        raise

    except Exception as e:
        logger.exception(f"Failed to initialize OpenSearch connection: {str(e)}")
        raise


class OpenSearchClusterUpdater:
    def __init__(self, index: str):
        self.client = opensearch_connection()
        self.index = index

    def fetch_clusters_with_null_label(self) -> List[Dict[str, Any]]:
        query = {
            "query": {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": "label"
                        }
                    }
                }
            },
            "sort": [
                {
                    "cluster_id": {
                        "order": "asc"
                    }
                }
            ],
            "_source": ["cluster_id", "children"]
        }

        response = self.client.search(index=self.index, body=query, size=1000)
        return response['hits']['hits']

    def fetch_clusters_by_ids(self, cluster_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not cluster_ids:
            return {}

        query = {
            "query": {
                "terms": {
                    "cluster_id": cluster_ids
                }
            },
            "_source": ["cluster_id", "label", "description"]
        }

        response = self.client.search(index=self.index, body=query, size=1000)
        return {
            doc["_source"]["cluster_id"]: {
                "label": doc["_source"].get("label"),
                "description": doc["_source"].get("description")
            }
            for doc in response['hits']['hits']
        }

    def update_cluster(self, cluster_id: str, label: str, description: str):
        update_body = {
            "doc": {
                "label": label,
                "description": description
            }
        }

        try:
            self.client.update(index=self.index, id=cluster_id, body=update_body)
            logger.info(f"Updated cluster {cluster_id} with label and description.")
        except Exception as e:
            logger.error(f"Failed to update cluster {cluster_id}: {e}")

    def process(self):
        null_label_clusters = self.fetch_clusters_with_null_label()

        for cluster_doc in null_label_clusters:
            source = cluster_doc["_source"]
            cluster_id = source["cluster_id"]
            children_ids = source.get("children", [])

            if not children_ids:
                continue

            child_data = self.fetch_clusters_by_ids(children_ids)

            if not child_data:
                continue

            child_labels = [d["label"] for d in child_data.values() if d.get("label")]
            child_descriptions = [d["description"] for d in child_data.values() if d.get("description")]

            if not child_labels or not child_descriptions:
                continue

            label_desc = self.get_cluster_metadata(child_labels, child_descriptions)

            if label_desc and label_desc.get("label") and label_desc.get("description"):
                self.update_cluster(cluster_id, label_desc["label"], label_desc["description"])

    def get_cluster_metadata(
        self, child_labels: List[str], child_descriptions: List[str]
    ) -> Dict[str, Any]:
        """
        Generate metadata (label and description) for a parent cluster using OpenAI.

        Args:
            child_labels (List[str]): List of child cluster labels.
            child_descriptions (List[str]): Corresponding descriptions for child clusters.

        Returns:
            Dict[str, Any]: Dictionary with keys: 'label', 'description'. May include error details.
        """
        topic_blocks = [
            f"Topic {i+1}: {label} – {desc}"
            for i, (label, desc) in enumerate(zip(child_labels, child_descriptions))
        ]
        topics_str = "\n".join(topic_blocks)

        prompt = (
            f"You are given several topics and their descriptions:\n\n"
            f"{topics_str}\n\n"
            f"Generate a JSON object with:\n"
            f"- 'label': A concise topic label using **at most three words**, summarizing the topic clearly. Do not use punctuation.\n"
            f"- 'description': A short informative sentence of **at most 15 words** that summarizes the combined meaning of all topics.\n\n"
            f"Return only a valid JSON object and nothing else."
        )

        try:
            response = openai_client.chat.completions.create(
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
            
            # 🧹 Remove Markdown code block wrappers if present
            if content.startswith("```") and content.endswith("```"):
                lines = content.split("\n")
                # Remove first and last line (e.g., ```json and ```)
                content = "\n".join(lines[1:-1]).strip()
            
            return json.loads(content)

        except Exception as e:
            logger.warning(f"OpenAI metadata generation failed: {e}")
            return {
                "label": None,
                "description": None,
                "error": f"Failed to parse JSON: {e}",
                "raw_output": content if 'content' in locals() else ""
            }


if __name__ == "__main__":
    updater = OpenSearchClusterUpdater(INDEX_NAME)
    updater.process()