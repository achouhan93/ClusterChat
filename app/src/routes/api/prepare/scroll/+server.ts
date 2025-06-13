
import { Client } from '@opensearch-project/opensearch';
import { json } from '@sveltejs/kit';
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

export async function POST({ request }) {
	try {

		const requestBody = await request.json()

		const scroll_limit: number = Number(requestBody.scroll_limit);
		if (scroll_limit < 10_000 || scroll_limit > 1_000_000)
			throw new Error('Invalid scroll_limit: must be between 10,000 and 1,000,000.');

		const scrollId: string = requestBody.scroll_id
		const scrollTime : string = requestBody.scroll_time
		let allDocs:any[] = []
		let hits = []
		const startTime = Date.now();

		// Scroll loop
		do {
			const scrollResponse = await client.scroll({
				scroll_id: scrollId,
				scroll: scrollTime
			});

			hits = scrollResponse.body.hits.hits;
			if (hits.length === 0) break;

			allDocs.push(...hits.map((hit: any) => hit._source));

			const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
			process.stdout.write(`\rFetched: ${allDocs.length} Points | Time: ${elapsedSeconds}s`);
		
		} while (hits.length > 0 && allDocs.length < scroll_limit)


			

		return json(allDocs)
	} catch (err: any) {
		console.error('OpenSearch Scroll Error:', err);
		return new Response(`Error: ${err.message}`, { status: 500 });
	}
}