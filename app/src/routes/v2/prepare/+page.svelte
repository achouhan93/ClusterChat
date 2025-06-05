<script lang="ts">
	import { downloadCosmographData } from 'cosmograph-v2';
	import type { CosmographDataPrepConfig } from 'cosmograph-v2';

	let requestedPoints: number = 10000;
	let error: string = '';

	async function getPointsFromOpenSearch() {
	if (requestedPoints < 10000 || requestedPoints > 5_000_000) {
		error = "Value Must be Between 10000 and 5000000";
		return;
	} else {
		error = '';
	}

	const res = await fetch(`/api/prepare/${requestedPoints}`);
	if (!res.ok) {
		error = `Server error: ${res.status}`;
		return;
	}

	// Read full response as text (slow for large!)
	const text = await res.text();

	let documents;
	try {
		documents = JSON.parse(text);
	} catch(e) {
		error = 'Failed to parse server response';
		return;
	}

	const config: CosmographDataPrepConfig = {
		outputFormat: 'arrow',
		points: {
			pointIdBy: 'document_id',
			pointXBy: 'x',
			pointYBy: 'y',
			pointLabelBy: 'title',
			pointClusterBy: 'cluster_id',
			pointIncludeColumns: ['date']
		}
	};

	const cosmographConfig = await downloadCosmographData(config, documents);

	console.log('Files downloaded!', cosmographConfig);
}


</script>

<form on:submit={getPointsFromOpenSearch}>
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