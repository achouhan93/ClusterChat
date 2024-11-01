<script lang="ts">
	import '../app.css';
	import 'open-props/style';
	import 'open-props/normalize';
	import 'open-props/buttons';
	import 'open-props/animations';
	import { Combine, BringToFront, LoaderCircle, BoxSelect } from 'lucide-svelte';
	import ChatInterface from '$lib/components/chat/ChatInterface.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import { toggleMultipleClustersMode, toggleHierachicalLabels,  fitViewofGraph, selectMultipleClusters } from '$lib/graph';
	import { onMount } from 'svelte';
	import { dataloaded } from '$lib/readcluster';
	import InfoView from '$lib/components/graph/InfoView.svelte';

	let isResizingVertical = false;
    let isResizingHorizontal = false;
	let initialInfoHeight = 40; // Default info height percentage
	let initialMousePositionY = 0;


    function handleVerticalResizeStart(event: MouseEvent) {
        isResizingVertical = true;
        document.body.style.cursor = "ew-resize";
		document.documentElement.classList.add("smooth-resize");
    }

    function handleHorizontalResizeStart(event: MouseEvent) {
        isResizingHorizontal = true;
        document.body.style.cursor = "ns-resize";
		document.documentElement.classList.add("smooth-resize");

    	initialMousePositionY = event.clientY;
    	initialInfoHeight = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--info-height")) || 40;
    }

    function handleMouseMove(event: MouseEvent) {
        if (isResizingVertical) {
            // Calculate width as a percentage of the viewport width
            const newChatWidth = (event.clientX / window.innerWidth) * 100;
            const clampedChatWidth = Math.min(40, Math.max(30, newChatWidth)); // Restrict between 20% and 40%
            document.documentElement.style.setProperty("--chat-width", `${clampedChatWidth}%`);
        }

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
        isResizingVertical = false;
        isResizingHorizontal = false;
        document.body.style.cursor = "default";
    }


	onMount(async () => {
		$dataloaded = true;
		const { createGraph, createTimeline } = await import('$lib/graph');
		createGraph();
		createTimeline();

		// Resizable Handles
		window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);

	});
</script>

<main id="main-frame">
	{#if !$dataloaded}
		<div class="loader"><LoaderCircle size="48" /></div>
	{:else}
		<div id="main-graph"> 
			<svg id="selection-svg"/>
		</div>
		<div id="main-search-bar" class="cosmograph-search">
			<SearchBar />
		</div>
		<div class="control-buttons">
			<button id="multiple-node-btn" class={$selectMultipleClusters ? "btn active" : "btn"} on:click={toggleMultipleClustersMode} title="Multiple Cluster Selection"
			><Combine /></button
			>
			<button id="hierachical-label" class="btn" on:click={toggleHierachicalLabels} title="Toggle Hierarchical Cluster Label"
			><BringToFront/></button
			>
			<button id="fitview-btn" class="btn" on:click={fitViewofGraph} title = "Fit View of Graph"
			><BoxSelect /></button
			>
		</div>

			<div id="chat-interface" ><ChatInterface /></div>

			<div id="info-view" >
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
		grid-template-columns: var(--chat-width) minmax(150px, 20%) 1fr 1fr;
		grid-template-rows: 15% var(--info-height)  1fr 10%;
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
	}

	    /* Resize Handles */
		.resize-handle-vertical {
        grid-column: 2;
        cursor: col-resize;
        background-color: #ccc;
        width: 5px;
        height: 100%;
        z-index: 3;
		position: absolute;
    }

    .resize-handle-horizontal {
        grid-row: 3;
        cursor: row-resize;
        background-color: #ccc;
        height: 3px;
        width: 100%;
        z-index: 3;
    }
	.smooth-resize {
        transition: none;
    }
</style>
