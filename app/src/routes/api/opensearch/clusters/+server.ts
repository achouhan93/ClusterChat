import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	CLUSTER_CHAT_CLUSTER_INFORMATION_INDEX,
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
		const startTime = Date.now();
		let allDocs:any[] = []
		const response = await client.search({
			index: CLUSTER_CHAT_CLUSTER_INFORMATION_INDEX,
			body: {
				query: {
					match_all: {}
				},
				_source:{
					includes: ['cluster_id','x', 'y', 'depth','label','is_leaf','path']
				},
				size: 20000
			}
		});
		
		const hits = response.body.hits.hits;
		if (hits.length === 0) throw("Error: While Fetching Clusters from OpenSearch");

		allDocs.push(...hits.map((hit: any) => hit._source));
		
		const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
		process.stdout.write(`\rFetched: ${allDocs.length} Points | Time: ${elapsedSeconds}s`);

		return new Response(JSON.stringify(allDocs));
	} catch (error) {
		console.error('Error:', error);
		return new Response(`Error: ${error}`, { status: 404 });
	}
}

