<script lang="ts">
	import { Search } from 'lucide-svelte';
	import { getRenderedNodes, getSelectedNodes, setSelectedNodes, updateGraphData, updateNodes } from '$lib/graph';
	import type { Node } from '$lib/types';

	async function fetchSearchQueryAnswer(search_query:string, search_accessor:string){
		/* Requests OpenSearch and fetches to 10k nodes */
		try {
			const response = await fetch(`/api/opensearch/search/${search_accessor}/${search_query}`);
			const data = await response.json();
			return data
		} catch(error) {
			console.error('Error fetching Answer for Search Query:', error);
			return null
		}
	}

	async function handleSearch(event: Event) {
		const form = event.currentTarget as HTMLFormElement;
		const formData = new FormData(form);

		const searchQuery = formData.get('search-query') as string;
		const searchAccessor = formData.get('search-accessor') as string;

		if (!searchQuery) return;

		// send to opensearch and get the top 10k
		const data = await fetchSearchQueryAnswer(searchQuery, searchAccessor);

		if (Array.isArray(data)){
			const nodeIdsToSelect:Set<string> = new Set(data.map(item => item._id));
			if(getSelectedNodes()?.length ===0 && getSelectedNodes() != undefined){
			// get all nodes with these ids
			const nodesToSelect:Node[] = getRenderedNodes().filter(node => nodeIdsToSelect.has(node.id))
			
			// updates the nodes to render
			updateNodes(nodesToSelect)
			updateGraphData()
			setSelectedNodes(nodesToSelect)
			} else if (getSelectedNodes() != undefined && getSelectedNodes() != null && getSelectedNodes()?.length != 0) {
				const nodesToSelect:Node[] = getSelectedNodes().filter(node => nodeIdsToSelect.has(node.id))
				setSelectedNodes(nodesToSelect)
			}

		}

		
	}


</script>


	<form on:submit|preventDefault={handleSearch}>
		<div class="search-bar-elems">
		<input
		id="search-query"
		autocomplete="off"
		type="textarea"
		placeholder="Search..."
		name="search-query"
	/>
		<select name="search-accessor" id="search-accessor">
			<option value="abstract">Abstract</option>
			<option value="title">Title</option>
		</select>
	</div>
	</form>


<style>
	.search-bar-elems {
		display: flex;
		direction: rows;
		margin-top: var(--size-3);
		gap: var(--size-1);
		margin-right: var(--size-2);
	}
	input {
		width: 80%;
		background-color: var(--surface-2-light);
		color: var(--text-2-light);
		transition: none !important;
		margin-left: var(--size-2);
		padding: var(--size-3);
	}
	input:focus-visible {
		transition: none !important;
	}
	#search-query {
		width: 75%;
		background-color: var(--surface-3-light);
	}
	#search-query:focus-visible {
		background-color: var(--surface-4-light);
		animation: var(--animation-scale-up) forwards;
	}
	/* #search-query:hover {
		
	} */
	#search-accessor {
		/* background-color: var(--surface-2-light); */
		/* color: var(--text-1-light); */
		background-color: #007bff;
		color: white;
		height: 100%;
		margin-left: var(--size-2);
		/* border-radius: var(--size-3); */
		border-radius: var(--radius-3); 
		/* background-color: #caf1f5; */
		padding: var(--size-1);
		/* Center align the text */
		text-align: center;
		text-align-last: center; /* For modern browsers to center the selected option */
		width: fit-content;
		padding: var(--size-3);
		
		/* Optional: Add some padding to ensure the text is vertically centered
		line-height: 1.5; */
	}
</style>
