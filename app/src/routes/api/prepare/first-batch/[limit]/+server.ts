/**
 * This script fetches the first batch to then be able to call the 
 * @returns Want to get the first batch , scrollId and scrollMinutes.
 * 
 */


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
            let firstBatch:any[] = []
            
            
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

            firstBatch.push(...hits.map((hit: any) => hit._source));

            const payload = {
                scroll_id: scrollId,
                scroll_time: scrollTime,
                hits: firstBatch
            };

            return new Response(JSON.stringify(payload), {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

    } catch (err: any) {
		console.error('OpenSearch Scroll Error:', err);
		return new Response(`Error: ${err.message}`, { status: 500 });

    }
}