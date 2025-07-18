import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
	OPENSEARCH_NODE
} from '$env/static/private';

// // Middleware
// app.use(cors());
// app.use(express.json());

// OpenSearch client setup
const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});

export async function POST({ request }) {
	try {
		// Log incoming request data
		const requestBody = await request.json();
		//console.log('Request body:', requestBody.cluster_ids);

		const ids: string[] = requestBody.doc_ids;

		if (!ids || !Array.isArray(ids) || ids.length === 0) {
			console.error('Invalid or missing IDs');
			return new Response('Invalid or missing IDs', { status: 400 });
		}

		// Perform the OpenSearch query
		const response = await client.search({
			index: CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
			body: {
				query: {
					terms: { document_id: ids }
				},
				_source: {
					includes: ['document_id', 'title']
				}
			}
		});

		return new Response(JSON.stringify(response.body.hits.hits), {
			headers: { 'Content-Type': 'application/json' }
		});
	} catch (error) {
		console.error('Error in POST handler:', error);
		return new Response('Error processing request', { status: 500 });
	}
}
