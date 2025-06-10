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
	import SearchBar from '$lib/components/v2/search/SearchBar.svelte';
	import InfoView from '$lib/components/v2/graph/InfoView.svelte';

  import { toggleMultipleClustersMode, toggleHierarchicalLabels, fitViewofGraph, startStreaming } from '$lib/v2/acceleratedGraph';

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
						intro: 'This tour will show you all the functionalities of this app.',
						position: 'center'
					},
					{
						element: document.getElementById('info-view'),
						intro: 'Here you can see information about each paper you hover over or click',
						position: 'right'
					},
					{
						element: document.getElementById('chat-interface'),
						intro: 'Here you can interact with the selected documents',
						position: 'right'
					},
					{
						element: document.querySelector('.toggle-container'),
						intro: 'Chat either with the selected Documents or the whole Corpus',
						position: 'right'
					},
					{
						element: document.querySelector('.menu-button'),
						intro: 'To start a new Chat session delete the old one',
						position: 'right'
					},
					{
						element: document.getElementById('main-search-bar'),
						intro: 'When searching for a specific paper use the search bar',
						position: 'bottom'
					},
					{
						element: document.querySelector('.search-options-part'),
						intro:
							'You can tailor your query using these options. Semantic Search is only possible on Abstracts.',
						position: 'bottom'
					},
					{
						element: document.getElementById('main-timeline'),
						intro: 'To select The documents based on the timeline you perform a drag selection',
						position: 'top'
					},
					{
						element: document.querySelector('.control-buttons'),
						intro: 'These buttons allow you to interact with the Graph directly',
						position: 'right'
					}
				]
			})
			.start();
	}

    onMount(async () => {
    try {
        const pointsFile = '/data/updated-cosmograph-points-combined-1.arrow'
        const configFile = '/data/cosmograph-config.json'
        const { createGraph, createTimeline, startStreaming, updateGraphDataInterval } = await import('$lib/v2/acceleratedGraph');
		$dataloaded = true;
        await createGraph(pointsFile,configFile)
        await createTimeline()
     
    } catch (err) {
        console.error('Error loading arrow file:', err);
    }
    
    
});

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
		<div id="main-graph"></div>
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





   

