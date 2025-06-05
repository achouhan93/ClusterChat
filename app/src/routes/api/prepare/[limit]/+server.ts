
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

export async function GET({ params }) {
	try {
		const batchSize: number = 10_000;
		const limit: number = Number(params.limit);
		if (limit < 10_000 || limit > 5_000_000)
			throw new Error('Invalid limit: must be between 10,000 and 5,000,000.');

		const scrollMinutes = Math.ceil(limit / 200_000);
		const scrollTime = `${scrollMinutes}m`;

		const startTime = Date.now();

		const encoder = new TextEncoder();

		const stream = new ReadableStream({
			async start(controller) {
				controller.enqueue(encoder.encode('['));

				let count = 0;

				// Initial search
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

				// Stream first batch
				for (const hit of hits) {
					if (count > 0) controller.enqueue(encoder.encode(','));
					controller.enqueue(encoder.encode(JSON.stringify(hit._source)));
					count++;
					if (count >= limit) break;
				}

				// Scroll loop
				while (hits.length > 0 && count < limit) {
					const scrollResponse = await client.scroll({
						scroll_id: scrollId,
						scroll: scrollTime
					});

					hits = scrollResponse.body.hits.hits;
					if (hits.length === 0) break;

					for (const hit of hits) {
						if (count >= limit) break;
						controller.enqueue(encoder.encode(','));
						controller.enqueue(encoder.encode(JSON.stringify(hit._source)));
						count++;

						const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
						process.stdout.write(`\rFetched: ${count} Points | Time: ${elapsedSeconds}s`);
					}
				}

				controller.enqueue(encoder.encode(']'));
				controller.close();
			}
		});

		return new Response(stream, {
			headers: {
				'Content-Type': 'application/json'
			}
		});
	} catch (err: any) {
		console.error('OpenSearch Scroll Error:', err);
		return new Response(`Error: ${err.message}`, { status: 500 });
	}
}