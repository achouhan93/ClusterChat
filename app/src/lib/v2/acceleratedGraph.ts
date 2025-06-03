// Cosmograph Imports
import type {
	CosmographConfig,
	CosmographTimelineConfig,
	CosmographDataPrepConfig
} from 'cosmograph-v2';
import { Cosmograph, CosmographTimeline } from 'cosmograph-v2';

import { type CosmosInputNode, type CosmosInputLink } from '@cosmograph/cosmos';

import {
	load10k,
	loadLables,
	getNodeColor,
	getAssociatedLeafs,
	LoadNodesByCluster
} from '../readcluster';

import {
	nodes,
	links,
	SelectedDateRange,
	SelectedSearchQuery,
	SelectedClusters,
	selectedNodes,
	selectMultipleClusters,
	hNode,
	hoveredNodeId,
	allClusters,
	allClusterNodes,
	ClustersTree,
	selectedNodesCount
} from '$lib/stores/nodeStore';

import { hierarchicalLabels, document_specific } from '$lib/stores/uiStore';

// Other
import '../app.css';
import type { Node, Link, Cluster } from '$lib/types';
//import { DragSelect } from '$lib/components/graph/DragSelect';
// import { dragSelection } from './components/graph/D3DragSelection';
import { get, derived } from 'svelte/store';

// Useful global variables
let graph: Cosmograph;
let timeline: CosmographTimeline;

let cachedIds = new Set<string>();
let lastSelected: Node[] = [];

/* ====================================== Graph and Timeline Event Handlers ====================================== */

/* ====================================== Config for the Graph and Timeline ====================================== */

const GraphConfig: CosmographConfig = {};

/* ====================================== Functions to Create Graph and Timeline ====================================== */

export function createGraph() {}

export function createTimeline() {}

// control buttons functions
export function toggleMultipleClustersMode() {}
export function toggleHierarchicalLabels() {}

/* ====================================== Graph Methods ====================================== */

async function initializeGraph() {}

export function updateGraphConfig(config: CosmographInputConfig<Node, Link>) {
	graph.setConfig(config);
}

// export function updateTimelineConfig(config: CosmographTimelineInputConfig)

export function updateGraphData() {
	// const startTime = new Date().getTime();
	// console.log('Updating the graph');
	// nodes.subscribe((nodesArray) => {
	//     graph.setData(nodesArray, get(links));
	// });
	// const endTime = new Date().getTime();
	// const duration = Math.round(endTime - startTime) / 1000;
	// console.log(`Time to set Data: ${duration} sec`);
}

export function updateNodes(newNodes: Node[]) {
	// make sure you update only unique
	// nodes.update((existingNodes) => {
	//     const existingIds = new Set(existingNodes.map((node) => node.id));
	//     const uniqueNewNodes = newNodes.filter((newNode) => !existingIds.has(newNode.id));
	//     return [...existingNodes, ...uniqueNewNodes];
	// });
}

export function selectNodesInRange(arr: [[number, number], [number, number]]) {
	// // TODO: fix this function
	// graph.selectNodesInRange(arr);
	// selectedNodes.set(getSelectedNodes() as Node[]);
}

export function unselectNodes() {
	// selectedNodes.set([]);
	// graph.unselectNodes();
	// SelectedDateRange.set(undefined);
	// const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
	// search_bar_input.value = '';
	// SelectedSearchQuery.set('');
	// SelectedClusters.set([]);
}

/**
 * Gets all the selected Node objects.
 * @return An array of selected Node objects.
 * @todo very slow for 5M Nodes, need another way.
 */

export function getSelectedNodes() {
	// return get(selectedNodes);
}

export function isSelectedNode(node: Node): boolean {
	// const current = getSelectedNodes();
	// // Rebuild the set only if the selection changed
	// if (current !== lastSelected) {
	//     cachedIds = new Set(current.map((n) => n.id));
	//     lastSelected = current;
	// }
	// return cachedIds.has(node.id);
}

export function getClusterNodes() {
	// return get(allClusterNodes);
}

export function getRenderedNodes() {
	// return get(nodes);
}

export function setSelectedNodes(nodes: Node[]) {
	// selectedNodes.set(nodes);
	// graph.selectNodes(get(selectedNodes));
	//graph.addNodesFilter()
}

export function setSelectedNodesOnGraph(nodes: Node[]) {
	// graph.selectNodes(nodes);
}

export function updateSelectedNodes(thenodes: Node[]) {
	// selectedNodes.update((existingNodes) => {
	//     const existingIds = new Set(existingNodes.map((n) => n.id));
	//     const uniqueNewNodes = thenodes.filter((newNode) => !existingIds.has(newNode.id));
	//     return [...existingNodes, ...uniqueNewNodes];
	// });
	// graph.selectNodes(getSelectedNodes());
}

export function conditionalSelectNodes(theNodes: Node[]) {
	// get the matches
	// const newNodes = new Set(theNodes.map((n) => n.id));
	// const nodesToShowonGraph = getSelectedNodes().filter((n) => newNodes.has(n.id));
	// setSelectedNodes(nodesToShowonGraph);
}

export function fitViewofGraph() {
	// graph.fitView();
}

function showLabelsfor(nodes: Node[]) {
	// if (nodes) {
	//     GraphConfig.showLabelsFor = nodes;
	//     updateGraphConfig(GraphConfig);
	// } else {
	//     GraphConfig.showLabelsFor = undefined;
	//     updateGraphConfig(GraphConfig);
	// }
}

// export function isSelectionActive(): boolean {
// 	return get(selectedNodesCount) !== 0;
// }

export let isSelectionActive = derived(selectedNodesCount, ($count) => $count !== 0);

export function getClusterNodesByClusterIds(cluster_ids: string[]): Node[] {
	// const ClusterNodeIds = new Set(cluster_ids);
	// const filteredNodes = getRenderedNodes().filter(
	//     (node) => ClusterNodeIds.has(node.id) && node.isClusterNode
	// );
	// return filteredNodes;
}
