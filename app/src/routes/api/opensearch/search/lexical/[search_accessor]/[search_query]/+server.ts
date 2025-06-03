import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
	OPENSEARCH_NODE
} from '$env/static/private';

// OpenSearch client setup
const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});

export async function GET({ params }) {
	try {
		const response = await client.search({
			index: CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
			body: {
				query: {
					match_phrase_prefix: {
						[params.search_accessor]: {
							query: params.search_query
						}
					}
				},
				_source: {
					includes: [params.search_accessor]
				},
				size: 10000
			}
		});
		return new Response(JSON.stringify(response.body.hits.hits));
	} catch (error) {
		console.error('Error fetching from OpenSearch:', error);
		return new Response('Error', { status: 404 });
	}
}
