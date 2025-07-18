<script lang="ts">
	import { X, Search } from 'lucide-svelte';
	import {
		getRenderedNodes,
		getSelectedNodes,
		setSelectedNodes,
		updateGraphData,
		updateNodes,
		conditionalSelectNodes,
		unselectNodes,

		isSelectedNode

	} from '$lib/graph';
	import { SelectedSearchQuery, isSelectionActive, searchInProgress, selectedNodes } from '$lib/stores/nodeStore';
	import { document_specific } from '$lib/stores/uiStore';
	import type { Node } from '$lib/types';
	import { getClusterNodes, setSelectedNodesOnGraph } from '$lib/graph';
	import { writable } from 'svelte/store';
	import { addToast } from '$lib/stores/toastStore';
	import { timeout } from 'd3';

	let checked_1 = writable<boolean>(false);
	// let checked_2=writable<boolean>(false)

	async function fetchSearchQueryAnswer(
		searchType: string,
		search_accessor: string,
		search_query: string
	) {
		/* Requests OpenSearch and fetches to 10k nodes */
		try {
			const response = await fetch(
				`/api/opensearch/search/${searchType}/${search_accessor}/${search_query}`
			);
			const data = await response.json();
			return data;
		} catch (error) {
			console.error('Error fetching Answer for Search Query:', error);
			return null;
		}
	}

	async function handleClearSearch() {
		// clear the input
		const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
		search_bar_input.value = '';
		SelectedSearchQuery.set('');
		unselectNodes()
	}

	async function handleSearch(event: Event) {
		if ($document_specific) {
			const form = event.currentTarget as HTMLFormElement;
			const formData = new FormData(form);

			const searchQuery = formData.get('search-query') as string;
			const searchType = formData.get('search-type') as string;
			const searchAccessor = formData.get('search-accessor') as string;

			if (!searchQuery || !searchType) return;
			if ($SelectedSearchQuery != '') unselectNodes();

			SelectedSearchQuery.set(searchQuery);

			searchInProgress.set(true)
			const data = await fetchSearchQueryAnswer(searchType, searchAccessor, searchQuery);
			console.dir(`Data from ${searchType} Search:`,data)
			if (Array.isArray(data) && data.length > 0) {
				await formatSearchData(data,searchType)
			} else {
				addToast({message:"No Search Results!", type:"error", dismissable:true, timeout:3000})
			}
			searchInProgress.set(false)
		} else {
			addToast({message:"Change to Docuemnt Specific!", type:"error", dismissable:true, timeout:3000})
		}
	}

	async function formatSearchData(data:any[],searchType:string){
		console.log("searchType:",searchType)
		const nodeIdsToSelect: Set<number> = searchType === "lexical"
		? new Set(data.map((item: any) => Number(item._id)))
		: new Set(data.map((item: any) => Number(item._source["documentID"])));
		console.log("nodeIdsToSelect:",nodeIdsToSelect)
		const theCurrentlySelectedNodes = getSelectedNodes()
		console.log("getSelectedNodes():",theCurrentlySelectedNodes.length)
		if (theCurrentlySelectedNodes?.length === 0 && theCurrentlySelectedNodes !== undefined) {
			// get all nodes with these ids
			const nodesToSelect: Node[] = getRenderedNodes().filter((node) =>	
				nodeIdsToSelect.has(node.id)
			);
			console.log("nodeIdsToSelect",nodeIdsToSelect)
			selectedNodes.set(nodesToSelect);
			const graphNodesToSelect = nodesToSelect.concat(getClusterNodes());
			setSelectedNodesOnGraph(graphNodesToSelect);
			isSelectionActive.set(true)
		} else if (
			theCurrentlySelectedNodes !== undefined &&
			theCurrentlySelectedNodes !== null &&
			theCurrentlySelectedNodes?.length !== 0
		) {
			const nodesToSelect: Node[] = theCurrentlySelectedNodes.filter((node) =>
				nodeIdsToSelect.has(node.id)
			);
			selectedNodes.set(nodesToSelect);
			const nodesToShowonGraph = nodesToSelect.concat(getClusterNodes());
			setSelectedNodesOnGraph(nodesToShowonGraph);
			isSelectionActive.set(true)
			console.log("I am here")
		}
	}
</script>

<form id="search-form" on:submit|preventDefault={handleSearch}>
	<div id="search-bar-container">
		<div id="search-bar-upper">
			<div class="search-icon"><Search /></div>
			<input id="search-bar-input" autocomplete="off" placeholder="Search..." name="search-query" />
			<button
				type="button"
				class="clear-search-btn"
				on:click|stopPropagation={handleClearSearch}
				title="Clear Chat"
			>
				<X size="40" /></button
			>
		</div>

		<div id="search-bar-options-container">
			<div class="toggle-btn-container">
				<input
					class="toggle-btns"
					type="hidden"
					name="search-type"
					value={$checked_1 ? 'semantic' : 'lexical'}
				/>
				<input type="checkbox" id="toggle-1" class="toggleCheckbox" bind:checked={$checked_1} />
				<label for="toggle-1" class="toggleContainer">
					<div>Lexical</div>
					<div>Semantic</div>
				</label>
			</div>

			<select name="search-accessor" id="search-accessor" form="search-form">
				{#if $checked_1}
					<option value="abstract">Abstract</option>
				{:else}
					<option value="abstract">Abstract</option>
					<option value="title">Title</option>
				{/if}
			</select>
		</div>
	</div>
</form>

<style>
	#search-bar-container {
		margin-top: var(--size-3);
		width: 95%;
		background: var(--surface-3-light);
		display: flex;
		flex-direction: column;
		border-radius: var(--radius-3);
	}

	#search-bar-input {
		width: 100%;
		padding: var(--size-3) 0 var(--size-3) 0;
		background-color: var(--surface-3-light);
		border-top-right-radius: var(--radius-3);
		color: var(--text-2-light);
		border-top-left-radius: var(--radius-3);
	}

	#search-bar-upper {
		display: flex;
	}

	.search-icon {
		/* display: flex; */
		min-width: 6%;
		align-self: center;
		justify-items: center;
		color: var(--gray-6);
	}

	#search-bar-options-container {
		display: flex;
		flex-direction: row;
		gap: var(--size-3);
		padding: 0 var(--size-1) var(--size-1) 0;
		align-items: center;
		margin-left: var(--size-3);
	}

	#search-bar-input:hover {
		cursor: text;
	}
	.clear-search-btn {
		background-color: #dee2e6;
		color: var(--text-2-light);
		width: -moz-fit-content;
		width: fit-content;
		min-width: 5%;
		border: none;
		transition: background-color 0.3s ease;
		box-shadow: none;
		border-radius: var(--radius-3);
		text-shadow: none;
		color: var(--gray-8);
	}
	.clear-search-btn:hover {
		background-color: var(--gray-4);
	}

	.clear-search-btn:active {
		background-color: var(--gray-5);
	}

	#search-accessor {
		background-color: #007bff;
		color: white;
		border-radius: var(--radius-6);
		/* background-color: #caf1f5; */
		text-align: center;
		text-align-last: center; /* For modern browsers to center the selected option */
		width: auto;
		border: 1px solid #ccc;
		/* font-weight: bold; */
		font-size: small;
		border: none;
	}

	/* .search-options-part{
		display: flex;
		flex-direction: column;
		align-items: center;
	} */

	.toggleContainer {
		position: relative;
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		width: max-content;
		border: 1px solid #f0f0f0;
		border-radius: var(--radius-6);
		/* background: #343434; */
		background: white;
		/* font-weight: bold; */
		font-size: small;
		color: #343434;
		cursor: pointer;
		margin: var(--size-px-1);
		width: 100%;
	}
	.toggleContainer::before {
		content: '';
		position: absolute;
		width: 50%;
		height: 100%;
		left: 0%;
		border-radius: var(--radius-6);
		background: #007bff;
		transition: all 0.3s;
	}
	.toggleCheckbox:checked + .toggleContainer::before {
		left: 50%;
	}
	.toggleContainer div {
		padding: 6px;
		text-align: center;
		z-index: 1;
	}
	.toggleCheckbox {
		display: none;
	}
	.toggleCheckbox:checked + .toggleContainer div:first-child {
		color: var(--text-2-light);
		transition: color 0.3s;
	}
	.toggleCheckbox:checked + .toggleContainer div:last-child {
		color: white;
		transition: color 0.3s;
	}
	.toggleCheckbox + .toggleContainer div:first-child {
		color: white;
		transition: color 0.3s;
	}
	.toggleCheckbox + .toggleContainer div:last-child {
		color: var(--text-2-light);
		transition: color 0.3s;
	}
</style>
