import { Client } from '@opensearch-project/opensearch';
import { json } from '@sveltejs/kit';
import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	OPENSEARCH_NODE,
	CLUSTER_TALK_DOCUMENT_INFORMATION_INDEX,
	CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_COMPLETE
} from '$env/static/private';

const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});

export async function GET({ params }) {
	try {
		const searchQuery = params.search_query;

		// Step 1: Call FastAPI to get embedding
		const embeddingResponse = await fetch('http://localhost:8100/embed', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ query: searchQuery })
		});
		if (!embeddingResponse.ok) throw new Error('Failed to fetch embedding from FastAPI');
		const { embedding } = await embeddingResponse.json();

		// Step 2: Perform vector search using embedding
		const vectorResponse = await client.search({
			index: CLUSTER_TALK_OPENSEARCH_TARGET_INDEX_COMPLETE, //testing
			body: {
				size: 10000,
				query: {
					knn: {
						pubmed_bert_vector: {
							vector: embedding,
							k: 100
							// TODO: change to threshold
						}
					}
				},
				_source: ['documentID', 'title', 'abstract_chunk']
			}
		});

		return json(vectorResponse.body.hits.hits);
	} catch (error) {
		console.error('Error performing semantic search:', error);
		return new Response('Semantic search error', { status: 500 });
	}
}
