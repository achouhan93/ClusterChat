import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	CLUSTER_TALK_DOCUMENT_INFORMATION_INDEX,
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
			index: CLUSTER_TALK_DOCUMENT_INFORMATION_INDEX,
			body: {
				query: {
					match_all: {}
				},
				from: params.from,
				size: params.size,
				_source: {
					includes: ["document_id","x","y","title","date","cluster_id"]
				}
			}
		});
		return new Response(JSON.stringify(response.body.hits.hits));
	} catch (error) {
		console.error('Error:', error);
		return new Response('Error', { status: 404 });
	}
}
