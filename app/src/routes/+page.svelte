<script lang="ts">
	import '../app.css';
	import 'open-props/style';
	import 'open-props/normalize';
	import 'open-props/buttons';
	import 'open-props/animations';
	import { SquareStack, SquareDashedMousePointer, LoaderCircle, BoxSelect } from 'lucide-svelte';
	import ChatInterface from '$lib/components/chat/ChatInterface.svelte';
	// import ClusterView from '$lib/components/cluster/ClusterView.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import { toggleMultipleNodesMode, toggleDragSelection, fitViewofGraph } from '$lib/graph';
	import { onMount } from 'svelte';
	import { dataloaded } from '$lib/readcluster';
	import InfoView from '$lib/components/graph/InfoView.svelte';

	onMount(async () => {
		$dataloaded = true;
		const { createGraph, createTimeline } = await import('$lib/graph');
		createGraph();
		createTimeline();
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
			<button id="multiple-node-btn" class="btn" on:click={toggleMultipleNodesMode}
				><SquareStack /></button
			>
			<button id="select-node-range-btn" class="btn" on:click={toggleDragSelection}
				><SquareDashedMousePointer /></button
			>
			<button class="btn" on:click={fitViewofGraph}>
				<BoxSelect />
			</button>
		</div>

		<div id="chat-interface"><ChatInterface /></div>
		<div id="info-view"><InfoView/></div>
		<!-- <div id="cluster-view">
			<ClusterView/>
		</div> -->
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
		grid-template-columns: 35% 15% 25% 25%;
		grid-template-rows: 15% 45% 30% 10%;
		grid-template-areas:
			'chat control-btns . search-bar'
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
	}
	#info-view {
		grid-area: info;
		height: 100%;
		z-index: 2;
		background-color: var(--surface-3-light);
	}
	/* #cluster-view {
		grid-area: cluster-view;
		z-index: 2;
		color: var(--text-1-light);
		max-width: fit-content;
		overflow-y: auto;
		background-color: rgb(255, 255, 255);
		opacity: 0%;
		box-shadow: inset;
		display: flex;
		flex-wrap: wrap;
		flex-direction: column;
	} */

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
</style>
