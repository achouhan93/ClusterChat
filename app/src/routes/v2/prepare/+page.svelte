<script lang="ts">
	import { downloadCosmographData } from 'cosmograph-v2';
	import type { CosmographDataPrepConfig } from 'cosmograph-v2';

	async function generateFiles() {
		const res = await fetch('/api/prepare');
		const documents = await res.json();

		const config:CosmographDataPrepConfig = {
			outputFormat: 'arrow',
			points: {
				pointIdBy: 'document_id',
				pointXBy: 'x',
				pointYBy: 'y',
				pointLabelBy: 'title',
				pointIncludeColumns: ['date']
			}
		};

		
		const cosmographConfig = await downloadCosmographData(config, documents);

		console.log('Files downloaded!', cosmographConfig);
	}
</script>

<button on:click={generateFiles}>
	Download Cosmograph Data
</button>
<input type="number" step="10000" id="n_points" name="number_of_points" min="10000" max="5_000_000">
<label for="n_points">between 10K and 5M Points</label>

