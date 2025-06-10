<script lang="ts">
	import { downloadCosmographData, prepareCosmographData } from 'cosmograph-v2';
	import type { CosmographDataPrepConfig } from 'cosmograph-v2';
	import { getColorForCluster } from '$lib/readcluster';

	let requestedPoints: number = 10000;
	let error: string = '';




	async function fetchFirstBatch(limit:number) {
		const res = await fetch(`/api/prepare/first-batch/${limit}`)
		if (!res.ok) {
			error = `Server error: ${res.status}`;
			return;
		}

		const payload = await res.json()
		return payload
	}

	async function fetchOtherBatches(payload:JSON) {
		const res = await fetch('/api/prepare/scroll', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},

		body: JSON.stringify(payload) // Send the array in the request body as JSON
	});
		const data = await res.json();
		return data
	}

	async function checkLimit() {
		if (requestedPoints < 10000 || requestedPoints > 5_000_000) {
			error = "Value Must be Between 10000 and 5000000";
			return;
		} else {
			error = '';
		}
	}
	function getBatchSizes(total, batchSize) {
		const batches = [];
		while (total > 0) {
			const currentBatch = Math.min(batchSize, total);
			batches.push(currentBatch);
			total -= currentBatch;
		}
		return batches;
	}

	async function getPointsFromOpenSearchinBatches() {
		checkLimit()

		const first = await fetchFirstBatch(requestedPoints)
		const batchSize = 1_000_000
		const batchSizes = getBatchSizes(requestedPoints,batchSize)
		const numberOfBatches = batchSizes.length
		console.log(batchSizes)

			for (let i=0; i < numberOfBatches; i++){
				
				const remaining = requestedPoints -i * batchSize;
				const scroll_limit = batchSizes[i];
			
				const sendPayload = {
					scroll_id : first.scroll_id,
					scroll_time : first.scroll_time,
					scroll_limit: scroll_limit
				}


				const config: CosmographDataPrepConfig = {
					outputFormat: 'arrow',
					points: {
						pointIdBy: 'document_id',
						pointXBy: 'x',
						pointYBy: 'y',
						pointLabelBy: 'title',
						pointClusterBy: 'cluster_id',
						pointIncludeColumns: ['date'],
						pointColorBy: 'cluster_id',
						pointColorByFn: (v:string) => getColorForCluster(v),
						outputFilename: `cosmograph-points-batch-${i+1}`
					}
				};

				if (requestedPoints > 10_000) {
					const documents = await fetchOtherBatches(sendPayload)
					const cosmographConfig = (i===0)? await downloadCosmographData(config,documents.concat(first.hits)) : await downloadCosmographData(config,documents)
				} else {
					const cosmographConfig = await downloadCosmographData(config, first.hits)
				}

				console.log(`Downloaded Batch ${i+1}/${numberOfBatches}`);
			}
}



</script>

<form on:submit={getPointsFromOpenSearchinBatches}>
	<label for="n_points">Number of Points (between 10K and 5M)</label>
	<input
		type="number"
		id="n_points"
		name="npoints"
		bind:value={requestedPoints}
		step="10000"
		min="10000"
		max="5000000"
		required
	/>
	<button type="submit">Download Cosmograph Data</button>
	{#if error}
		<p style="color: red;">{error}</p>
	{/if}
</form>