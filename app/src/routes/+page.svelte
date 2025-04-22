<script lang="ts">
	import '../app.css';
	import 'open-props/style';
	import 'open-props/normalize';
	import 'open-props/buttons';
	import 'open-props/animations';
	import { Combine, BringToFront, LoaderCircle, BoxSelect, Binoculars } from 'lucide-svelte';
	import ChatInterface from '$lib/components/chat/ChatInterface.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import { toggleMultipleClustersMode, toggleHierarchicalLabels,  fitViewofGraph, selectMultipleClusters } from '$lib/graph';
	import { onMount } from 'svelte';
	import { dataloaded } from '$lib/readcluster';
	import InfoView from '$lib/components/graph/InfoView.svelte';
	import introJs from 'intro.js';
	import 'intro.js/minified/introjs.min.css';





	function startTour() {
	introJs().setOptions({
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
			intro: 'You can tailor your query using these options. Semantic Search is only possible on Abstracts.',
			position: 'bottom'
		},
		{
			element: document.getElementById('main-timeline'),
			intro: 'To select The documents based on the timeline you perform a drag selection',
			position: 'top'
		},
		{
			element: document.querySelector(".control-buttons"),
			intro: 'These buttons allow you to interact with the Graph directly',
			position: 'right'
		}
	]
		}).start();
	}




    let isResizingHorizontal = false;
	let initialInfoHeight = 40; // Default info height percentage
	let initialMousePositionY = 0;


    function handleHorizontalResizeStart(event: MouseEvent) {
        isResizingHorizontal = true;
        document.body.style.cursor = "ns-resize";
		document.documentElement.classList.add("smooth-resize");

    	initialMousePositionY = event.clientY;
    	initialInfoHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--info-height")) || 40;
    }

    function handleMouseMove(event: MouseEvent) {
        // if (isResizingVertical) {
        //     // Calculate width as a percentage of the viewport width
        //     const newChatWidth = (event.clientX / window.innerWidth) * 100;
        //     const clampedChatWidth = Math.min(40, Math.max(30, newChatWidth)); // Restrict between 20% and 40%
        //     document.documentElement.style.setProperty("--chat-width", `${clampedChatWidth}%`);
        // }

		if (isResizingHorizontal) {
        // Calculate the vertical delta from the starting position
        const deltaY = event.clientY - initialMousePositionY;
        
        // Adjust the pane height based on the delta
        const newInfoHeight = initialInfoHeight + (deltaY / window.innerHeight) * 100;
        
        // Clamp the new height within the desired range
        const clampedInfoHeight = Math.max(20, Math.min(50, newInfoHeight));
        
        // Apply the new height
        document.documentElement.style.setProperty("--info-height", `${clampedInfoHeight}%`);
    }
    }

    function handleMouseUp() {
        //isResizingVertical = false;
        isResizingHorizontal = false;
        document.body.style.cursor = "default";
    }


	onMount(async () => {
		$dataloaded = true;
		const { createGraph, createTimeline } = await import('$lib/graph');
		createGraph();
		createTimeline();

	});

	onMount(() => {
				// Resizable Handles
				window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);
		return () => {
            // Cleanup listeners on component unmount
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
        };
	})


</script>

<main id="main-frame">
	{#if !$dataloaded}
		<div class="loader"><LoaderCircle size="48" /></div>
	{:else}
		<div id="main-graph"> 
			<svg id="selection-svg"/>
		</div>
		<div id="main-search-bar" class="cosmograph-search" >
			<SearchBar />
		</div>
		<div class="control-buttons">
			<button id="multiple-node-btn" class={$selectMultipleClusters ? "btn active" : "btn"} on:click={toggleMultipleClustersMode} title="Multiple Cluster Selection"
			><Combine /> Multiple Cluster Select</button
			>
			<button id="hierarchical-label" class="btn" on:click={toggleHierarchicalLabels} title="Toggle Hierarchical Cluster Label"
			><BringToFront/> Hierarchical Labels</button
			>
			<button id="fitview-btn" class="btn" on:click={fitViewofGraph} title = "Fit View of Graph"
			><BoxSelect /> Fit View</button
			>
			<button id="start-tour-btn" class="btn" on:click={startTour} title= "Start Tour"
			><Binoculars/>  Tour</button
			>
		</div>

			<div id="chat-interface" ><ChatInterface /></div>

			<div id="info-view">
				<div
				class="resize-handle-horizontal"
				role="button"
				tabindex="0"
				on:mousedown={handleHorizontalResizeStart}
				aria-label="Resize sidebar"
			></div>
			<InfoView/></div>
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
	#main-frame {
		display: grid;
		/* grid-template-columns: var(--chat-width, 35%) minmax(auto,15%) minmax(auto,25%) minmax(auto,25%); */
		grid-template-columns: max(35%) minmax(150px, 20%) 1fr 1fr;
		grid-template-rows: 15% var(--info-height,40%)  1fr max(10%);
		grid-template-areas:
			'chat control-btns search-bar search-bar'
			'chat . . .'
			'info . . .'
			'info timeline timeline timeline';
	}
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
		transition: width 0.2s ease-in-out;
	}
	#info-view {
		grid-area: info;
		height: 100%;
		z-index: 2;
		background-color: var(--surface-3-light);
		overflow-y: auto;
		overflow-x: hidden;
		transition: height 0.2s ease-in-out;
	}
	#multiple-node-btn.active{
		background-color: var(--surface-1-dark);
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
