<script lang="ts">
	import { Search, X } from 'lucide-svelte';
	import { getRenderedNodes, getSelectedNodes, setSelectedNodes, updateGraphData, updateNodes, SelectedSearchQuery, conditionalSelectNodes, unselectNodes, document_specific, selectedNodes } from '$lib/graph';
	import type { Node } from '$lib/types';
	import { getClusterNodes, setSelectedNodesOnGraph } from '$lib/graph';
	import Toggle from '$lib/components/search/Toggle.svelte';
	

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

	async function handleClearSearch (){
		// clear the input 
		const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
		search_bar_input.value = '';
		SelectedSearchQuery.set('')
	}
	async function handleSearch(event: Event) {
		if (document_specific){
		const form = event.currentTarget as HTMLFormElement;
		const formData = new FormData(form);

		const searchQuery = formData.get('search-query') as string;
		const searchAccessor = formData.get('search-accessor') as string;

		if (!searchQuery) return;
		if ($SelectedSearchQuery != "") unselectNodes()
		
		SelectedSearchQuery.set(searchQuery)


		// send to opensearch and get the top 10k
		const data = await fetchSearchQueryAnswer(searchQuery, searchAccessor);

		if (Array.isArray(data)){
			const nodeIdsToSelect:Set<string> = new Set(data.map(item => item._id));
			if(getSelectedNodes()?.length ===0 && getSelectedNodes() != undefined){
				// get all nodes with these ids
				const nodesToSelect:Node[] = getRenderedNodes().filter(node => nodeIdsToSelect.has(node.id))
				selectedNodes.set(nodesToSelect)
				const graphNodesToSelect = nodesToSelect.concat(getClusterNodes())
				setSelectedNodesOnGraph(graphNodesToSelect)

			} else if (getSelectedNodes() != undefined && getSelectedNodes() != null && getSelectedNodes()?.length != 0) {
				// TODO
				const nodesToSelect:Node[] = getSelectedNodes().filter(node => nodeIdsToSelect.has(node.id))
				selectedNodes.set(nodesToSelect)
				const nodesToShowonGraph = nodesToSelect.concat(getClusterNodes())
				setSelectedNodesOnGraph(nodesToShowonGraph)
			}

		}
	} else {
		alert("Change to Document Specific!")
	}
		
	}


</script>


	<form on:submit|preventDefault={handleSearch}>
		<div class="search-bar-elems">
		

		<button type="button" class="clear-search-btn" on:click|stopPropagation={handleClearSearch} title='Clear Chat'>	
		<X size="48"/></button>

		<input
		id="search-bar-input"
		autocomplete="off"
		type="textarea"
		placeholder="Search..."
		name="search-query"
	/>
		<div class="search-options-part">
			<Toggle/>
		<select name="search-accessor" id="search-accessor">
			<option value="abstract">Abstract</option>
			<option value="title">Title</option>
		</select>
	</div>
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
	#search-bar-input {
		width: 100%;
		background-color: var(--surface-3-light);
	}
	#search-bar-input:focus-visible {
		background-color: var(--surface-4-light);
	}
	#search-bar-input:hover {
		cursor: text;
	}
	/* #search-query:hover {
		
	} */
	#search-accessor {

		background-color: #007bff;
		color: white;
		height: 70%;
		font-size:12px;
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
		border: 1px solid #ccc;
		
		/* Optional: Add some padding to ensure the text is vertically centered
		line-height: 1.5; */
	}
	.clear-search-btn {
		background-color: var(--blue-4);
		color: white;
		width:fit-content;
		height: max-content;
		border: none;
		align-self: center;
	}
	.search-options-part{
		display: flex;
		flex-direction: column;
		align-items: center;
	}
</style>
