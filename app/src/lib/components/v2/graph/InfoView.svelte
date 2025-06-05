<script lang="ts">
    import { getSelectedPointCount, getSelectedPointIndices, unselectAllPoints, setArrayofSelectedPointIds } from '$lib/v2/acceleratedGraph';
	import {
		selectedNodes,
		SelectedDateRange,
		SelectedSearchQuery,
		SelectedClusters,
		hNode,
		allClusters,
		ClustersTree,
		selectedClustersCount,
        isSelectionActive,
        selectedPointsIds,

		numberOfSelectedPoints

	} from '$lib/stores/nodeStore';

    import { pageCount } from '$lib/stores/uiStore';

	import { ChevronRight, ChevronLeft, X, ExternalLink } from 'lucide-svelte';
	import { get, writable } from 'svelte/store';
	import { type Node, type Cluster, type InfoPanel, undefinedCluster } from '$lib/types';


	let currentPage = writable<number>(1);
	let currentInfoPanel = writable<InfoPanel>([]);

	let showMoreCluster: boolean = false;
	let showMoreAbstract: boolean = false;

    function toggleShowMoreAbstract() {
    showMoreAbstract = !showMoreAbstract;
	}
	const handleLeftClick = () => {
		if ($currentPage != 1) currentPage.update((value) => value - 1);
	};

	const handleRightClick = () => {
		if ($currentPage != $numberOfSelectedPoints) currentPage.update((value) => value + 1);
	};

    const handleClearTags = () => {
        // Reverse Selection (maybe make a variable that stores the selection from the search)
        SelectedDateRange.set(undefined);
        SelectedSearchQuery.set('');
        SelectedClusters.set([]);
        unselectAllPoints();
	};

    async function fetchInfoPanelById(pointId: string) {
		// getting ["abstract","authors:name","keywords:name","journal:title"]
		// have pubmed id, title, cluster id, date
		const response = await fetch(`/api/opensearch/infoview/${pointId}`);
		const data = await response.json();

		const currentInfo: InfoPanel[] = data.map(
			(item:any) =>
				({
					pubmed_id: item._id, // change to node.id after test
					title: item._source['title'],
					abstract: item._source['abstract'],
					date: item._source['date'] || undefined,
					cluster_top: ["cluster","cluster","cluster"],//getClusterInformationFromNode(node),
					authors_name: item._source['authors:name'],
					journal_title: item._source['journal:title'],
					keywords: item._source['keywords:name']
				}) satisfies InfoPanel
		);
		currentInfoPanel.set(currentInfo[0]);
	}

    function getClusterLabelById(){}
    function formatDateRange(date: [Date,Date]) {}
    // function getClusterInformationFromNode(){}


 $: if($selectedPointsIds.length !== 0) {
    
    fetchInfoPanelById($selectedPointsIds[$currentPage -1])
 }
$: if ($isSelectionActive && $numberOfSelectedPoints > 0) {
    (async () => {
        await setArrayofSelectedPointIds(getSelectedPointIndices());
    })();
}
</script>
<div class="node-information-view">
	<h4>Node Information</h4>
	<div class="node-info-list">
                				

			

		{#if $isSelectionActive && $numberOfSelectedPoints > 0}
            <div class="pagation-btns">
					<button class="pagation-btn" on:click={handleLeftClick}><ChevronLeft /></button>
					<button class="pagation-btn" on:click={handleRightClick}><ChevronRight /></button>
					{$currentPage} of {$numberOfSelectedPoints}
				</div>

			<div class="info-field">
				<span class="info-field-title">Pubmed ID</span>
				<div class="info-field-content">
					<a
						href={`https://pubmed.ncbi.nlm.nih.gov/${$currentInfoPanel.pubmed_id}`}
						target="_blank"
						rel="noopener noreferrer"
						>{$currentInfoPanel.pubmed_id} <sup><ExternalLink size="12" /></sup></a
					>
				</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Title</span>
				<div class="info-field-content">{$currentInfoPanel.title}</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Abstract</span>
				<div class="info-field-content {showMoreAbstract ? '' : 'collapsed'}">
					{$currentInfoPanel.abstract}
				</div>
				<button class="toggle-button" on:click={toggleShowMoreAbstract}>
					{showMoreAbstract ? 'Read Less' : 'Read More'}
				</button>
			</div>
<!--TODO: make cluster dynamic -->
            			<div class="info-field">
				<span class="info-field-title">Cluster</span>
				<div class="info-field-content">
					<ul class="topic-list">
						{#each $currentInfoPanel.cluster_top ?? [] as topic, index}
							<li class="topic-item-{index}">{topic}</li>
						{/each}
					</ul>
				</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Date</span>
				<div class="info-field-content">{$currentInfoPanel.date}</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Author's Names</span>
				<div class="info-field-content">
					{#each $currentInfoPanel.authors_name ?? [] as author, index}
						{author}{#if index < $currentInfoPanel.authors_name.length - 1},&nbsp{/if}
					{/each}
				</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Journal Title</span>
				<div class="info-field-content">{$currentInfoPanel.journal_title}</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Keywords</span>
				<div class="info-field-content">{$currentInfoPanel.keywords}</div>
			</div>
		{/if}
	</div>
</div>

<style>
	h4 {
		color: black;
		text-align: center;
		align-self: center;
		padding: var(--size-2);
	}
	.node-information-view {
		display: flex;
		flex-direction: column;
	}
	.info-field {
		margin: var(--size-2);
		display: flex;
		flex-direction: column;
	}
	.info-field-title {
		color: var(--blue-8);
		font-weight: var(--font-weight-8);
		padding: var(--size-2);
		size: var(--font-size-1);
	}
	.info-field-content {
		height: fit-content;
		font-size: small;
		padding: var(--size-2);
		color: var(--text-1-light);
		background-color: var(--surface-4-light);
		border-radius: var(--radius-2);
	}
	.info-field-content a {
		display: flex;
		color: var(--blue-5);
	}
	.info-field-content.collapsed {
		overflow-y: scroll; /* Allows vertical scrolling */
		overflow-x: hidden;
		height: var(--size-fluid-5);
		display: flex;
	}
	.pagation-btns {
		margin-bottom: var(--size-2);
		margin-left: var(--size-1);
		gap: var(--size-2);
		display: flex;
		font-size: small;
		align-items: center;
	}
	.filter-tags {
		display: flex;
		flex-direction: row;
		gap: var(--size-1);
	}
	.pagation-btn {
		background-color: var(--blue-8);
		height: fit-content;
		max-height: var(--size-px-1);
	}
	.selected-date-range {
		width: fit-content;
		padding: var(--size-2);
		border-radius: var(--radius-5);
		background-color: var(--blue-4);
		font-size: small;
	}
	.selected-search {
		width: fit-content;
		padding: var(--size-2);
		border-radius: var(--radius-5);
		background-color: var(--green-4);
		font-size: small;
	}
	.selected-cluster {
		width: fit-content;
		padding: var(--size-2);
		border-radius: var(--radius-5);
		background-color: var(--red-4);
		font-size: small;
	}
	.clear-btn {
		border-radius: var(--radius-6);
		max-width: fit-content;
		background-color: inherit;
		align-self: center;
		transition: background-color 0.3s ease;
	}
	.clear-btn:active {
		background-color: var(--surface-4-light);
	}
	.toggle-button {
		color: #0073e6;
		background-color: inherit;
		cursor: pointer;
		font-size: x-small;
		margin-top: var(--size-1);
		display: inline-block;
		align-self: left;
	}
	span {
		padding: var(--size-1);
	}
	button {
		box-shadow: none;
		border: hidden;
		text-shadow: none;
	}
	button:hover {
		box-shadow: none;
	}
	button:focus-visible {
		border: none;
		box-shadow: none;
	}
	.topic-list {
		list-style-type: none; /* Remove default bullet points */
		padding-left: 1.5em; /* Indent the items */
		font-size: smaller;
	}

	.topic-item-0:before {
		content: '• '; /* Add bullet manually */
		color: darkred; /* Adjust color as you like */
	}
	.topic-item-1:before {
		content: '•• '; /* Add bullet manually */
		color: darkred; /* Adjust color as you like */
	}

	.topic-item-2:before {
		content: '••• '; /* Add bullet manually */
		color: darkred; /* Adjust color as you like */
	}
</style>
