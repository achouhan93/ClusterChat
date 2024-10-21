import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	OPENSEARCH_INDEX,
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

export async function GET() {
	try {
		const response = await client.search({
			index: OPENSEARCH_INDEX,
            scroll: "1m",
            size: 10000,
			body: {
				query: {
					match_all: {}
				},
			}
		});
		return new Response(JSON.stringify(response.body/* .hits.hits */));
	} catch (error) {
		console.error('Error:', error);
		return new Response('Error', { status: 404 });
	}
}
