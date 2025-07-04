<script lang="ts">
	import '../../app.css';
	import 'open-props/style';
	import 'open-props/normalize';
	import 'open-props/buttons';
	import 'open-props/animations';

	import { Combine, BringToFront, LoaderCircle, BoxSelect, Binoculars, Menu } from 'lucide-svelte';

	import introJs from 'intro.js';
	import 'intro.js/minified/introjs.min.css';

	import ChatInterface from '$lib/components/chat/ChatInterface.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import InfoView from '$lib/components/graph/InfoView.svelte';

	import { toggleMultipleClustersMode, toggleHierarchicalLabels, fitViewofGraph } from '$lib/graph';

	import { hierarchicalLabels } from '$lib/stores/uiStore';
	import { selectMultipleClusters, dataloaded } from '$lib/stores/nodeStore';
	import { onMount } from 'svelte';

	let sideCollapsed = false;

	$: gridTemplateAreas = sideCollapsed
		? `'control-btns . . search-bar'
		'. '
		'.'
		'timeline`
		: `'chat control-btns . search-bar'
		'chat . . .'
		'info . . .'
		'info timeline timeline timeline'`;

	$: gridTemplateColumns = sideCollapsed
		? '0 minmax(200px, 12%) 1fr 1fr'
		: 'max(35%) minmax(200px, 12%) 0.5fr 1.5fr';

	function startTour() {
		introJs()
			.setOptions({
				steps: [
					{
						element: document.getElementById('main-graph'),
						intro: 'Welcome to ClusterChat! This system enables advanced corpus exploration through interactive cluster visualization. This main view represents the cluster visualisation of the document corpus, where each node corresponds to a document and clusters represent groups derived using semantic embeddings.',
						position: 'center'
					},
					{
						element: document.getElementById('info-view'),
						intro: 'This panel displays detailed metadata for the document you hover over or select. It includes document id, publication year, journal, authorship, and more—providing immediate context for your exploration.',
						position: 'right'
					},
					{
						element: document.getElementById('chat-interface'),
						intro: 'This chat interface allows you to ask natural language questions either at the document level or across the entire corpus. It is powered by a Retrieval-Augmented Generation (RAG) pipeline.',
						position: 'right'
					},
					{
						element: document.querySelector('.toggle-container'),
						intro: 'Use this toggle to switch between two modes of question answering: querying the selected documents or querying the entire corpus.',
						position: 'right'
					},
					{
						element: document.querySelector('.menu-button'),
						intro: 'Use this menu to manage your chat sessions. If you wish to begin a new session, you can clear the previous one here to maintain context precision.',
						position: 'right'
					},
					{
						element: document.getElementById('main-search-bar'),
						intro: 'You can locate specific set of documents using the search bar. This supports keyword-based (lexical) search on titles and abstracts, as well as semantic search on abstracts using embeddings.',
						position: 'bottom'
					},
					{
						element: document.getElementById('main-timeline'),
						intro: 'This timeline enables temporal filtering. Drag-select a time interval to narrow down documents by their publication date—useful for identifying recent trends or historical shifts.',
						position: 'top'
					},
					{
						element: document.querySelector('.control-buttons'),
						intro: 'These controls let you interact with the visualization. You can zoom, reposition, and re-center the view to better inspect particular clusters or documents.',
						position: 'right'
					}
				]
			})
			.start();
	}

	let isResizingHorizontal = false;
	let initialInfoHeight = 40; // Default info height percentage
	let initialMousePositionY = 0;

	function handleHorizontalResizeStart(event: MouseEvent) {
		isResizingHorizontal = true;
		document.body.style.cursor = 'ns-resize';
		document.documentElement.classList.add('smooth-resize');

		initialMousePositionY = event.clientY;
		initialInfoHeight =
			parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--info-height')) ||
			40;
	}

	function handleMouseMove(event: MouseEvent) {
		if (isResizingHorizontal) {
			// Calculate the vertical delta from the starting position
			const deltaY = event.clientY - initialMousePositionY;

			// Adjust the pane height based on the delta
			const newInfoHeight = initialInfoHeight + (deltaY / window.innerHeight) * 100;

			// Clamp the new height within the desired range
			const clampedInfoHeight = Math.max(20, Math.min(50, newInfoHeight));

			// Apply the new height
			document.documentElement.style.setProperty('--info-height', `${clampedInfoHeight}%`);
		}
	}

	function handleMouseUp() {
		//isResizingVertical = false;
		isResizingHorizontal = false;
		document.body.style.cursor = 'default';
	}

	onMount(async () => {
		$dataloaded = true;
		const { createGraph, createTimeline } = await import('$lib/graph');
		createGraph();
		createTimeline();

	});

	onMount(() => {
		// Resizable Handles
		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', handleMouseUp);
		return () => {
			// Cleanup listeners on component unmount
			window.removeEventListener('mousemove', handleMouseMove);
			window.removeEventListener('mouseup', handleMouseUp);
		};
	});

	async function toggleSide() {
		sideCollapsed = !sideCollapsed;
	}

</script>
<main
	id="main-frame"
	style="
		display: grid;
		grid-template-areas: {gridTemplateAreas};
		grid-template-columns: {gridTemplateColumns};
		grid-template-rows: 15% var(--info-height, 40%) 1fr max(10%);
		transition: grid-template-columns 700ms var(--ease-5);
	"
>
	{#if !$dataloaded}
		<div class="loader"><LoaderCircle size="48" /></div>
	{:else}
		<div id="main-graph">
			<svg id="selection-svg" />
		</div>
		<div id="main-search-bar" class="cosmograph-search">
			<SearchBar />
		</div>
		<div class="control-buttons">
			<button id="collapse-btn" class="btn rollout-button" on:click={toggleSide} title="Start Tour"
				><span class="icon"><Menu /></span><span class="label"
					>{sideCollapsed ? 'Show Side' : 'Collapase Side'}</span
				></button
			>
			<button
				id="multiple-node-btn"
				class="btn rollout-button"
				on:click={toggleMultipleClustersMode}
				title={$selectMultipleClusters
					? 'Multiple Cluster Selection is active'
					: 'Single Cluster Selection is active'}
				><span class="icon"><Combine /></span><span class="label"
					>{$selectMultipleClusters ? 'Select Single Clusters' : 'Select Multiple Clusters'}</span
				></button
			>
			<button
				id="hierarchical-label"
				class="btn rollout-button"
				on:click={toggleHierarchicalLabels}
				title="Toggle Hierarchical Cluster Label"
				><span class="icon"><BringToFront /></span><span class="label"
					>{$hierarchicalLabels ? 'Flat Labels' : 'Hierarchical Labels'}</span
				></button
			>
			<button
				id="fitview-btn"
				class="btn rollout-button"
				on:click={fitViewofGraph}
				title="Fit View of Graph"
				><span class="icon"><BoxSelect /></span><span class="label">Fit View</span></button
			>
			<button id="start-tour-btn" class="btn rollout-button" on:click={startTour} title="Start Tour"
				><span class="icon"><Binoculars /></span><span class="label">Tour</span></button
			>
		</div>

		<div id="chat-interface" style={sideCollapsed ? 'width:0; overflow:hidden;' : 'width:100%;'}>
			<ChatInterface />
		</div>

		<div id="info-view" style={sideCollapsed ? 'width: 0; overflow:hidden;' : 'width:100%'}>
			<div
				class="resize-handle-horizontal"
				role="button"
				tabindex="0"
				on:mousedown={handleHorizontalResizeStart}
				aria-label="Resize sidebar"
			></div>
			<InfoView />
		</div>
		<!-- <div
			class="resize-handle-vertical"
			role="button"
			tabindex="0"
			on:mousedown={handleVerticalResizeStart}
			aria-label="Resize sidebar"
		></div> -->

		<div id="main-timeline" class="cosmograph-timeline"></div>
	{/if}
	<slot />
</main>

<style>
	#main-graph,
	#main-frame {
		height: 100%;
		width: 100%;
		position: absolute;
		scroll-behavior: smooth;
		background-color: #fff;
	}
	/* #main-frame {
		display: grid;

		grid-template-columns: max(35%) minmax(200px, 12%) 0.5fr 1.5fr;
		grid-template-rows: 15% var(--info-height,40%)  1fr max(10%);
		grid-template-areas:
			'chat control-btns . search-bar'
			'chat . . .'
			'info . . .'
			'info timeline timeline timeline';
	} */

	#main-search-bar {
		grid-area: search-bar;
		height: 100%;
		z-index: 2;
	}
	#main-timeline {
		grid-area: timeline;
		min-height: 0;
		height: 100%;
		z-index: 2;
	}
	#chat-interface {
		grid-area: chat;
		z-index: 2;
		border-bottom: solid 1px #fff;
		height: 100%;
		transition: width 0.5s var(--ease-5);
	}
	#info-view {
		grid-area: info;
		height: 100%;
		z-index: 2;
		background-color: var(--surface-3-light);
		overflow-y: auto;
		overflow-x: hidden;
		transition: width 0.5s var(--ease-5);
	}
	.loader {
		animation: var(--animation-spin);
		animation-duration: 2s;
		animation-timing-function: linear;
		animation-iteration-count: infinite;
		position: fixed;
		top: 0;
		right: 0;
		width: 100%;
		height: 100%;
		display: flex;
		justify-content: center;
		align-items: center;
		cursor: wait;
		background-color: #fff;
		color: #000;
	}
	.control-buttons {
		z-index: 2;
		align-items: flex-start;
		grid-area: control-btns;
		display: flex;
		flex-direction: column;
		scale: 0.9;
		gap: var(--size-1);
		margin-top: var(--size-1);
	}
	.control-buttons button {
		background-color: #007bff;
		color: white;
		box-shadow: none;
		border: none;
		text-shadow: none;
		font-size: 14px;
		font-weight: 600;
	}

	.rollout-button {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 50px;
		height: 40px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 5px;
		font-family: sans-serif;
		cursor: pointer;
		overflow: hidden;
		padding: 0 10px;
		transition: width 0.3s ease;
	}

	.rollout-button:hover {
		width: 100%;
	}

	.icon {
		z-index: 1;
		font-size: 20px;
		flex-shrink: 0;
	}

	.label {
		position: relative;
		left: 40px; /* Start to the right of the icon */
		white-space: nowrap;
		display: none;
		transform: translateX(-30px);
		transition:
			opacity 0.3s ease,
			transform 0.3s ease;
	}

	.rollout-button:hover .label {
		display: block;
		transform: translateX(-30px);
	}
	.rollout-button:hover .icon {
		display: none;
	}

	#start-tour-btn {
		background-color: var(--red-7);
	}

	/* Resize Handles */
	/* .resize-handle-vertical {
        grid-column: 2;
        cursor: col-resize;
        background-color: #ccc;
        width: 5px;
        height: 100%;
        z-index: 3;
		position: absolute;
    } */

	.resize-handle-horizontal {
		grid-row: 3;
		cursor: row-resize;
		background-color: #ccc;
		height: 3px;
		width: 100%;
		z-index: 3;
	}
	/* .smooth-resize {
        transition: none;
    } */

</style>
