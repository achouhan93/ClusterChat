import { json } from '@sveltejs/kit';
import { Client } from '@opensearch-project/opensearch';
import {
	OPENSEARCH_NODE,
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX
} from '$env/static/private';

const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});


export async function GET() {
// 	const result = await client.search({
// 		index: CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
// 		body: {
// 			query: { match_all: {} },
// 			_source: {
// 				includes: ['document_id', 'x', 'y', 'title', 'date', 'cluster_id']
// 			}
// 		},
// 		size: 10000
// 	});

// 	const documents = result.body.hits.hits.map((hit: any) => hit._source);

// 	return json(documents);

	try {
		const batchSize = 10_000;
		const limit = 1_000_000;
		const scrollTime = '5m';
		let allDocs: any[] = [];

		// Step 1: Initial search with scroll
		let response = await client.search({
			index: CLUSTER_CHAT_DOCUMENT_INFORMATION_INDEX,
			scroll: scrollTime,
			size: batchSize,
			body: {
				query: { match_all: {} },
				_source: {
					includes: ['document_id', 'x', 'y', 'title', 'date', 'cluster_id']
				}
			}
		});

		let scrollId = response.body._scroll_id;
		let hits = response.body.hits.hits;

		allDocs.push(...hits.map((hit: any) => hit._source));

		// Step 2: Continue scrolling
		while (hits.length > 0 && allDocs.length < limit) {
			const scrollResponse = await client.scroll({
				scroll_id: scrollId,
				scroll: scrollTime
			});

			hits = scrollResponse.body.hits.hits;
			if (hits.length === 0) break;

			allDocs.push(...hits.map((hit: any) => hit._source));
			scrollId = scrollResponse.body._scroll_id;

			console.log(`Fetched: ${allDocs.length} documents`);
		}

		return json(allDocs);
	} catch (err: any) {
		console.error('OpenSearch Scroll Error:', err);
		return new Response(`Error: ${err.message}`, { status: 500 });
	}
}