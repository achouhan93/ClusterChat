<script lang="ts">
	import { unselectNodes } from '$lib/graph';
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

		searchInProgress

	} from '$lib/stores/nodeStore';

	import { Jumper } from 'svelte-loading-spinners';

	import { ChevronRight, ChevronLeft, X, ExternalLink } from 'lucide-svelte';
	import { get, writable } from 'svelte/store';
	import { type Node, type Cluster, type InfoPanel, undefinedCluster } from '$lib/types';

	let NodesToShow = writable<Node[]>([]);
	let currentPage = writable<number>(1);
	let pageCount = writable<number>(0);
	let currentInfoPanel = writable<InfoPanel>([]);

	let showMoreCluster: boolean = false;
	let showMoreAbstract: boolean = false;

	// Toggle function to show/hide content

	function toggleShowMoreAbstract() {
		showMoreAbstract = !showMoreAbstract;
	}
	const handleLeftClick = () => {
		if ($currentPage != 1) currentPage.update((value) => value - 1);
	};

	const handleRightClick = () => {
		if ($currentPage != $pageCount) currentPage.update((value) => value + 1);
	};

	const handleClearTags = () => {
		// Reverse Selection (maybe make a variable that stores the selection from the search)
		SelectedDateRange.set(undefined);
		SelectedSearchQuery.set('');
		SelectedClusters.set([]);
		unselectNodes();
	};

	async function fetchInfoPanelByNode(node: Node) {
		// getting ["abstract","authors:name","keywords:name","journal:title"]
		// have pubmed id, title, cluster id, date
		const response = await fetch(`/api/opensearch/infoview/${node.id}`);
		const data = await response.json();

		const currentInfo: InfoPanel[] = data.map(
			(item) =>
				({
					pubmed_id: item._id, // change to node.id after test
					title: item._source["title"],
					abstract: item._source["abstract"],
					date: item._source["date"] || undefined,
					cluster_top: getClusterInformationFromNode(node),
					authors_name: item._source['authors:name'],
					journal_title: item._source['journal:title'],
					keywords: item._source['keywords:name']
				}) satisfies InfoPanel
		);
		currentInfoPanel.set(currentInfo[0]);
	}

	function getClusterLabelById(cluster_id: string) {
		const foundCluster = get(allClusters).find((cluster) => cluster.id === cluster_id);
		if (foundCluster != undefined) return foundCluster.label;

		return 'error';
	}
	function formatDateRange(date: [Date, Date]) {
		if (date[0].getFullYear() === date[1].getFullYear()){
			return `${date[0].toLocaleString('en-US', { month: 'short' })} ${date[0].getDate()} -  
        	${date[1].toLocaleString('en-US', { month: 'short' })} ${date[1].getDate()}, ${date[1].getFullYear()}`;
		} else {
			return `${date[0].toLocaleString('en-US', { month: 'short' })} ${date[0].getDate()}, ${date[0].getFullYear()} -  
        	${date[1].toLocaleString('en-US', { month: 'short' })} ${date[1].getDate()}, ${date[1].getFullYear()}`;
		}

	}
	function getClusterRange(cluster_path: string[], searchCluster: string): string[] {
		const index = cluster_path.indexOf(searchCluster);
		if (index === 0) {
			return [cluster_path[0], cluster_path[1], cluster_path[2]];
		} else if (index === 1) {
			return [cluster_path[1], cluster_path[2], cluster_path[3]];
		}
		return [cluster_path[index - 2], cluster_path[index - 1], cluster_path[index]];
	}

	function getClusterInformationFromNode(node: Node): string[] {
		const cluster_id: string = node.cluster;
		const theClusters: Cluster[] = get(allClusters);
		const clusterinfo: Cluster =
			theClusters.find((cluster) => cluster.id === cluster_id && cluster.isLeaf) ??
			undefinedCluster;
		const clusterLinage = new Set(clusterinfo.path.split('/') /* .slice(-3) */);
		const foundClusters = theClusters.filter((cluster) => clusterLinage.has(cluster.id));
		foundClusters.sort((c1, c2) => c2.depth - c1.depth);
		const foundClusterName: string[] = foundClusters.map((c) => c.label);
		if ($SelectedClusters.length !== 0) {
			const selected_cluster: Cluster =
				theClusters.find((cluster) => cluster.id === $SelectedClusters[0]) ?? undefinedCluster;
			return getClusterRange(foundClusterName, selected_cluster.label);
		} else {
			return getClusterRange(foundClusterName, clusterinfo.label);
		}
	}

	selectedNodes.subscribe((newnodes) => {
		NodesToShow.set(newnodes);
		if ($selectedNodes.length == 0) {
			pageCount.set(0);
		} else {
			pageCount.set(newnodes.length);
		}
	});

	hNode.subscribe((n) => {
		if (!n || $hNode?.isClusterNode) return;

		console.log(`isSelectionActive: ${get(isSelectionActive)}`)
		if ($isSelectionActive) {
			const nodes = get(NodesToShow);
			const foundNodeIndex = nodes.findIndex((node) => node.id === n.id);

			if (foundNodeIndex !== -1) {
				const currentPageVal = $currentPage;
				const newPageIndex = foundNodeIndex + 1;

				// Only update if needed
				if (newPageIndex !== currentPageVal) {
					currentPage.set(newPageIndex);
				}

				fetchInfoPanelByNode(nodes[foundNodeIndex]);
			} else {
				console.warn('Node not found in NodesToShow:', n);
			}
		} else {
			NodesToShow.set([$hNode]);
		}
	});

	// TODO: update
	$: if ($NodesToShow.length != 0) {
		fetchInfoPanelByNode(get(NodesToShow)[$currentPage - 1]);
	}
</script>

<div class="node-information-view">
	<h4>Node Information</h4>
	<div class="node-info-list">

		{#if $NodesToShow.length !== 0 && !$NodesToShow[$currentPage - 1].isClusterNode}
			{#if $NodesToShow.length > 1}
				<div class="pagation-btns">
					<button class="pagation-btn" on:click={handleLeftClick}><ChevronLeft /></button>
					<button class="pagation-btn" on:click={handleRightClick}><ChevronRight /></button>
					{$currentPage} of {$pageCount}
				</div>
			{/if}

			<!-- {#if get(isSelectionActive)} -->
			{#if $SelectedDateRange !== undefined || $SelectedSearchQuery !== '' || $SelectedClusters.length !== 0}
				<div class="filter-tags">
					{#if $SelectedDateRange !== undefined}
						<div class="selected-date-range">
							<span><b>Date:</b> {formatDateRange($SelectedDateRange)}</span>
						</div>
					{/if}

					{#if $SelectedSearchQuery !== ''}
						<div class="selected-search">
							<span><b>Search:</b> {$SelectedSearchQuery}</span>
						</div>
					{/if}

					{#if $SelectedClusters.length !== 0}
						<div class="selected-cluster">
							{#if $SelectedClusters.length === 1}
								<span><b>Cluster:</b> {getClusterLabelById($SelectedClusters[0])}</span>
							{:else}
								<span
									><b>Clusters:</b>{$SelectedClusters.map(getClusterLabelById).join(', ')}</span
								>
							{/if}
						</div>
					{/if}

					<button class="clear-btn" on:click={handleClearTags}><X /></button>
				</div>
			{/if}

			<div class="info-field">
				<span class="info-field-title">Pubmed ID</span>
				<div class="info-field-content">
					<a
						href={`https://pubmed.ncbi.nlm.nih.gov/${$currentInfoPanel.pubmed_id}`}
						target="_blank"
						rel="noopener noreferrer"
						>{$currentInfoPanel?.pubmed_id} <sup><ExternalLink size="12" /></sup></a
					>
				</div>
			</div>

			<div class="info-field">
				<span class="info-field-title">Title</span>
				<div class="info-field-content">{$currentInfoPanel?.title}</div>
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
		
		{:else if $searchInProgress}
			<div class="loading-container">
			<Jumper size="60" color="#007BFF" unit="px" duration="1s" />
			<p class="loading-text">
				search in progress...
			</p>
		</div>
		{/if}
	</div>
</div>

<style>
	h4 {
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
	  
	.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
	/* justify-content: center; 
	height: 100vh; */
	position: relative;
  }

  .loading-text {
    margin-top: 12px;
    font-size: 16px;
    color: var(--text-2-light);
  }
</style>
