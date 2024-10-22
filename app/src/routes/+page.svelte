<script lang="ts">
	import '../app.css';
	import 'open-props/style';
	import 'open-props/normalize';
	import 'open-props/buttons';
	import 'open-props/animations';
	import { SquareStack, SquareDashedMousePointer, LoaderCircle, BoxSelect } from 'lucide-svelte';
	import ChatInterface from '$lib/components/chat/ChatInterface.svelte';
	import { toggleMultipleNodesMode, toggleDragSelection, fitViewofGraph } from '$lib/graph';
	import { onMount } from 'svelte';
	import {load10k, dataloaded, nodes } from '$lib/readcluster';
	import { get } from 'svelte/store';
	onMount(async () => {
		$dataloaded=true
		const { createGraph, createTimeline } = await import('$lib/graph');
		createGraph();
		createTimeline();
		console.log(get(nodes))
	});
</script>

<main id="main-frame">
	{#if !$dataloaded}
		<div class="loader"><LoaderCircle size="48" /></div>
	{:else}
		<div id="main-graph"></div>
		<div id="main-search-bar" class="cosmograph-search"></div>
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
	}
	#main-frame {
		display: grid;
		grid-template-columns: 18% 32% 25% 25%;
		grid-template-rows: 10% 80% 10%;
		grid-template-areas:
			'chat search-bar search-bar search-bar'
			'chat . . .'
			'chat timeline timeline timeline';
	}
	#main-search-bar {
		grid-area: search-bar;
	}
	#main-timeline {
		grid-area: timeline;
	}
	#chat-interface {
		grid-area: chat;
		z-index: 2;
		border-right: solid 1px #ffffff1c;
	}

	.control-buttons {
		position: absolute;
		bottom: 160px;
		right: 10px;
		display: flex;
		flex-direction: column;
		gap: var(--size-1);
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
	}
</style>
