// Cosmograph Imports
import type { CosmographInputConfig, CosmographTimelineInputConfig } from '@cosmograph/cosmograph';

import { type CosmosInputNode, type CosmosInputLink, Graph } from '@cosmograph/cosmos';
import { Cosmograph, CosmographTimeline } from '@cosmograph/cosmograph';
import {
	loadLabels,
	loadNodes,
	getNodeColor,
	getAssociatedLeafs,
	LoadNodesByCluster
} from './readcluster';

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
	selectedNodesCount,
	isSelectionActive
} from '$lib/stores/nodeStore';

import { hierarchicalLabels, document_specific } from '$lib/stores/uiStore';

// Other
import '../app.css';
import type { Node, Link, Cluster } from '$lib/types';
//import { DragSelect } from '$lib/components/graph/DragSelect';
// import { dragSelection } from './components/graph/D3DragSelection';
import { get, derived } from 'svelte/store';
import { range } from './utils';

// Useful global variables
let graph: Cosmograph<Node, Link>;
let timeline: CosmographTimeline<Node>;

const BATCH_SIZE: number = 10000;
const MAX_SIZE: number = 100000; // TODO: make this dynamic
const BATCH_NUMBER_START: number = 1; // TO CHANGE BEFORE PUSH
const INITIAL_BATCH_SIZE: number = BATCH_NUMBER_START * BATCH_SIZE;
const HOVERED_NODE_SIZE: number = 0.5;
// let $batch_number= writable<number>(BATCH_NUMBER_START);
// let $update_number=writable<number>(1);
export const INITIAL_FITVIEW: [[number, number], [number, number]] = [
	[10.784323692321777, 21.064863204956055],
	[12.669471740722656, 15.152010917663574]
];

let cachedIds = new Set<string>();
let lastSelected: Node[] = [];

/* ====================================== Graph and Timeline Event Handlers ====================================== */


/**
 * Handles click events on individual graph nodes.
 *
 * If filtering is not active and a document is currently selected, it:
 * - Shows the label for the clicked node.
 * - Selects the node in the graph visualization.
 * - Sets the clicked node as the current selection.
 *
 * If no node was clicked (e.g., background click), it:
 * - Clears the current node selection.
 *
 * @param {Node} clickedNode - The node that was clicked. Can be null or undefined if no node was selected.
 */
const handleNodeClick = async (clickedNode: Node) => {
	if (clickedNode && !get(isSelectionActive) && get(document_specific) && !clickedNode.isClusterNode) {
		showLabelsfor([clickedNode] as Node[]);
		graph.selectNode(clickedNode);
		setSelectedNodes([clickedNode]);
	} else if (!clickedNode) {
		unselectNodes();
	}
};

/**
 * Handles click events on a graph node label.
 *
 * If the clicked node represents a cluster and Single Cluster Selection is set:
 * - Sets the selected cluster.
 * - Retrieves associated leaf nodes.
 * - Loads all nodes belonging to the selected cluster.
 * - Filters currently rendered nodes by the cluster ID.
 * - Updates the selected nodes on the graph accordingly.
 *
 * @param {Node} node - The node object that was clicked. If it is a cluster node, its associated leaf nodes will be processed.
 *
 * @todo
 * Add MultiClusterSelection as an Option!
 */
const handleLabelClickSingle = async (node: Node) => {
	if (node.isClusterNode && node.id !== '') {
		if (get(SelectedClusters).length > 0) {
			selectedNodes.set([]);
			SelectedDateRange.set(undefined);
			const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
			search_bar_input.value = '';
			SelectedSearchQuery.set('');
			SelectedClusters.set([]);
			isSelectionActive.set(false)
		}

		SelectedClusters.set([node.id]);
		const cluster_id: string[] = getAssociatedLeafs(node.id, node.title);
		await LoadNodesByCluster(cluster_id);

		const set_cluster_id = new Set(cluster_id);
		const filteredNodes = getRenderedNodes().filter((node) => set_cluster_id.has(node.cluster));

		if (!get(isSelectionActive)) {
			selectedNodes.set(filteredNodes);
			filteredNodes.push(node);
			graph.selectNodes(filteredNodes);
			isSelectionActive.set(true)
		} else if (get(isSelectionActive)) {
			const filteredNodesSet = new Set(filteredNodes.map((node) => node.id));
			const nodesToShowonGraph = getSelectedNodes().filter((node) => filteredNodesSet.has(node.id));
			selectedNodes.set(nodesToShowonGraph);
			nodesToShowonGraph.push(node);
			graph.selectNodes(nodesToShowonGraph);
		}
	}
};

const handleLabelClickMultiple = async(node: Node) => {
	if (node.isClusterNode && node.id !== '') {
		SelectedClusters.update((clusters) => [...clusters, node.id]);
		console.log("handling Label Click...",node)
		const cluster_id: string[] = getAssociatedLeafs(node.id, node.title);
		LoadNodesByCluster(cluster_id);

		const set_cluster_ids = new Set(get(SelectedClusters));
		let filteredNodes:Node[] = getRenderedNodes().filter((node) => set_cluster_ids.has(node.cluster));

		selectedNodes.set(filteredNodes);
		filteredNodes.push(node);
		graph.selectNodes(filteredNodes);
		isSelectionActive.set(true)
	}

}


/**
 * Handles timeline range selection to filter and highlight nodes by date.
 *
 * When a valid time range is selected and nodes are rendered:
 * - Updates the selected date range if the selection is of `Date` type.
 * - Filters rendered nodes whose `date` field falls within the selected range.
 * - Updates selected nodes and highlights them on the graph.
 * - Includes cluster nodes in the selection for context.
 *
 * If there are already selected nodes, it intersects them with the time-filtered set.
 *
 * @param {[Date, Date] | [number, number]} selection - The selected date or numeric range from the timeline.
 */
const handleTimelineSelection = async (selection: [Date, Date] | [number, number]) => {
	if (getRenderedNodes().length != 0) {
		if (selection.length === 2 && selection[0] instanceof Date && selection[1] instanceof Date) {
			SelectedDateRange.set(selection);
		}

		const nodesToSelect: Node[] = getRenderedNodes().filter(
			(node) =>
				node.date != undefined &&
				new Date(node.date) >= selection[0] &&
				new Date(node.date) <= selection[1]
		);

		if (!get(isSelectionActive)) {
			//setSelectedNodes(nodesToSelect)
			selectedNodes.set(nodesToSelect);
			const graphNodesToSelect = nodesToSelect.concat(get(allClusterNodes));
			graph.selectNodes(graphNodesToSelect);
			isSelectionActive.set(true)
		} else {
			// TODO
			const nodesToSelectSet = new Set(nodesToSelect.map((node) => node.id));
			const nodesToShowonGraph = getSelectedNodes().filter((node) => nodesToSelectSet.has(node.id));
			selectedNodes.set(nodesToShowonGraph);
			const graphNodesToSelect = nodesToShowonGraph.concat(get(allClusterNodes));
			graph.selectNodes(graphNodesToSelect);
		}

		// TODO: for some reason the graph selection only appears,
		// when the user clicks outside the blue timeline selection box!
		// so setting the selection to [0,0] emulates that
		timeline.setSelection([0, 0]);
	}
};

const handleOnZoomStartHierarchical = async () => {
	const ZoomLevel: number = graph.getZoomLevel() || 10;
	let ClusterLabelsToShow: string[] = [];
	if (ZoomLevel < 50) {
		ClusterLabelsToShow = range(19,20).map((index) => get(ClustersTree)[index]).flat();
	} else if (ZoomLevel > 50 && ZoomLevel < 100) {
		ClusterLabelsToShow = range(17,18).map((index) => get(ClustersTree)[index]).flat();
	} else if (ZoomLevel > 100 && ZoomLevel < 150) {
		ClusterLabelsToShow = range(14,16).map((index) => get(ClustersTree)[index]).flat();
	} else if (ZoomLevel > 150 && ZoomLevel < 200){
		ClusterLabelsToShow = range(11,14).map((index) => get(ClustersTree)[index]).flat();
	} else if (ZoomLevel > 200 && ZoomLevel < 500) {
		ClusterLabelsToShow = range(5,10).map((index) => get(ClustersTree)[index]).flat();
	} else if (ZoomLevel > 500) {
		ClusterLabelsToShow = range(0,10).map((index) => get(ClustersTree)[index]).flat();
	}
	GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow);
	updateGraphConfig(GraphConfig);
	// console.log(ZoomLevel);
};



const handleOnZoomStartTopLabel = () => {

	const ZoomLevel: number = graph.getZoomLevel() || 10;
	let ClusterLabelsToShow: string[] = [];
	if (ZoomLevel < 50) {
		GraphConfig.showTopLabelsLimit = 10;
	} else if( ZoomLevel > 50 && ZoomLevel < 100) {
		GraphConfig.showTopLabelsLimit = 40
	} else if (ZoomLevel > 100 && ZoomLevel < 200) {
		GraphConfig.showTopLabelsLimit = 100
	} else if (ZoomLevel > 200 && ZoomLevel < 500) {
		GraphConfig.showTopLabelsLimit = Math.floor(ZoomLevel*10);
	} else if (ZoomLevel > 500) {
		GraphConfig.showTopLabelsLimit = get(allClusters).length;
	}
	GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow);
	updateGraphConfig(GraphConfig);


	// console.log(`ZoomLevel: ${ZoomLevel}, Label Limit: ${GraphConfig.showTopLabelsLimit}`);
	
};

async function getVisibleLabels(ZoomLevel,minLabels,maxLabels,zoomFactor) {
// Logarithmic scaling (smooth increase)
	const visibleLabels = Math.min(
		minLabels * Math.pow(zoomFactor, ZoomLevel - 30),
		maxLabels
	);
	console.log("Visible labels count:",Math.floor(visibleLabels))
	return Math.floor(visibleLabels);
}

/* ====================================== Config for the Graph and Timeline ====================================== */

export const GraphConfig: CosmographInputConfig<Node, Link> = {
	//backgroundColor: '#151515',
	backgroundColor: '#ffffff',
	nodeGreyoutOpacity: 0.005,
	//showFPSMonitor: true, /* shows performance monitor on the top right */
	nodeSize: (node: Node) => 0.05,
	nodeColor: (node: Node) => node.color,
	nodeLabelAccessor: (node: Node) => node.isClusterNode? node.title: '',
	//nodeLabelClassName: (node: Node) => node.isClusterNode ? `cosmograph-cluster-label-${node.date}` : 'cosmograph-node-label', // getNodeLabelClassName
	nodeLabelClassName: (node: Node) =>
		node.isClusterNode ? 'cosmograph-cluster-label' : 'cosmograph-node-label',
	nodeLabelColor: (node: Node) =>
		node.isClusterNode ? getNodeColor(node.x, node.y, INITIAL_FITVIEW, 1) : '#fff',
	// nodeLabelColor: (node:Node) => node.isClusterNode ? '#808080' : "#fff",
	hoveredNodeLabelColor: (node: Node) => (node.isClusterNode ? '#000' : node.color),
	hoveredNodeLabelClassName: 'cosmograph-hovered-node-label',
	hoveredNodeRingColor: '#2463EB',
	disableSimulation: true,
	renderLinks: false,
	scaleNodesOnZoom: true,
	fitViewOnInit: true,
	showDynamicLabels: false,
	showHoveredNodeLabel: false,
	showTopLabels: true,
	showTopLabelsValueKey: 'isClusterNode',

	onClick(clickedNode) {
		handleNodeClick(clickedNode as Node);
	},
	onLabelClick(node) {

	if (!get(selectMultipleClusters)) {
		handleLabelClickSingle(node);
	} else {
		handleLabelClickMultiple(node)
	}
		
	},
	// Scale node on hover
	onNodeMouseOver(hoveredNode) {
		// Deactivate hover if a selection is present
		if (hoveredNode) {
			if ((get(isSelectionActive) && isSelectedNode(hoveredNode)) || !get(isSelectionActive)) {
				hNode.set(hoveredNode);
				hoveredNodeId.set(hoveredNode.id); // Track the hovered node by ID
				const main_frame = document.getElementById('main-graph');
				main_frame.style.cursor = 'pointer';
				GraphConfig.nodeSize = (node: Node) =>
					node.id === get(hoveredNodeId) ? HOVERED_NODE_SIZE : 0.05;
				updateGraphConfig(GraphConfig); // Update the graph configuration to reflect the new node size
			}
		}
	},

	// Reset node size when mouse leaves the node
	onNodeMouseOut() {
		hoveredNodeId.set(''); // Reset the hovered node
		hNode.set(undefined);
		if (get(hNode) === undefined) console.log('Node Not Hovered');
		GraphConfig.nodeSize = (node: Node) =>
			node.id === get(hoveredNodeId) ? HOVERED_NODE_SIZE : 0.05;
		updateGraphConfig(GraphConfig); // Update the graph configuration to reset the node size
		const main_frame = document.getElementById('main-graph');
		main_frame.style.cursor = 'default';
	},
	// onZoom(){console.log(graph.getZoomLevel())},

	// TODO: DRAG SELECT DOESN'T WORK!
	// onMouseMove() {
	// 	if (drag_select) {
	// 		const container = document.getElementById('main-frame');
	// 		const containerCanvas = container?.querySelector('canvas') as HTMLCanvasElement;

	// 		if (containerCanvas) {
	// 			selectionArea = new DragSelect(containerCanvas)
	// 		}
	// 	}
	// },
	onZoomStart(e, userDriven) {
		handleOnZoomStartTopLabel()
	},
	onNodesFiltered(filteredNodes) {
		// console.log("Filtered Nodes: ")
		// console.log(filteredNodes)
	}
};

const TimelineConfig: CosmographTimelineInputConfig<Node> = {
	// accessor: (d) => (d.date ? new Date(d.date) : new Date('2024-01-01')),
	accessor: (d) => {
  if (!d.date) return new Date('2024-01-01');

  // If timestamp is in seconds, convert to ms:
  const timestamp = typeof d.date === 'number' && d.date < 10 ** 12
    ? d.date * 1000
    : d.date;

  return new Date(timestamp);
},
	tickStep: 15_778_560_000, // 6 months
	//axisTickHeight: 30,
	filterType: 'nodes',
	formatter(d) {
		// TO CHANGE FOR 4M
		return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
		//return "";
	},
	onSelection(selection) {
		if (selection) {
			handleTimelineSelection(selection);
		}
	}
};

/* ====================================== Functions to Create Graph and Timeline ====================================== */

export function createGraph() {
	const canvas = document.getElementById('main-graph') as HTMLDivElement;
	graph = new Cosmograph(canvas, GraphConfig);
	graph.setConfig(GraphConfig);
	initializeGraph();
}

export function createTimeline() {
	const timelineContainer = document.getElementById('main-timeline') as HTMLDivElement;
	timeline = new CosmographTimeline<Node>(
		graph as unknown as Cosmograph<CosmosInputNode, CosmosInputLink>,
		timelineContainer
	);
	timeline.setConfig(TimelineConfig);
}

// control buttons functions
export function toggleMultipleClustersMode() {
	selectMultipleClusters.update((value) => !value);
}
export function toggleHierarchicalLabels() {
		console.log("hierarchicalLables",hierarchicalLabels)
	if (get(hierarchicalLabels)) {
		GraphConfig.showTopLabels = true;
		GraphConfig.showLabelsFor = undefined;
		// GraphConfig.showTopLabelsLimit = 10;
		GraphConfig.showTopLabelsValueKey = 'isClusterNode';
		GraphConfig.nodeLabelClassName = (node: Node) =>
			node.isClusterNode ? 'cosmograph-cluster-label' : 'cosmograph-node-label';
		GraphConfig.onZoom = handleOnZoomStartTopLabel;
	} else {
		GraphConfig.showTopLabels = false;
		GraphConfig.showTopLabelsLimit = undefined;
		GraphConfig.showTopLabelsValueKey = undefined;
		GraphConfig.nodeLabelClassName = (node: Node) =>
			node.isClusterNode ? `cosmograph-cluster-label-${node.date}` : 'cosmograph-node-label';
		GraphConfig.onZoom = handleOnZoomStartHierarchical;
	}
	updateGraphConfig(GraphConfig);
	hierarchicalLabels.update((value) => !value);
}

/* ====================================== Graph Methods ====================================== */

async function initializeGraph() {
	await loadLabels();
	await loadNodes();
	graph.setData(get(nodes), get(links));
}

export function updateGraphConfig(config: CosmographInputConfig<Node, Link>) {
	graph.setConfig(config);
}

// export function updateTimelineConfig(config: CosmographTimelineInputConfig)

export function updateGraphData() {
	const startTime = new Date().getTime();
	console.log('Updating the graph');
	nodes.subscribe((nodesArray) => {
		graph.setData(nodesArray, get(links));
	});
	const endTime = new Date().getTime();
	const duration = Math.round(endTime - startTime) / 1000;
	console.log(`Time to set Data: ${duration} sec`);
}

export function updateNodes(newNodes: Node[]) {
	// make sure you update only unique
	nodes.update((existingNodes) => {
		const existingIds = new Set(existingNodes.map((node) => node.id));

		const uniqueNewNodes = newNodes.filter((newNode) => !existingIds.has(newNode.id));

		return [...existingNodes, ...uniqueNewNodes];
	});
}

export function selectNodesInRange(arr: [[number, number], [number, number]]) {
	// TODO: fix this function
	graph.selectNodesInRange(arr);
	selectedNodes.set(getSelectedNodes() as Node[]);
}

export function unselectNodes() {
	selectedNodes.set([]);
	graph.unselectNodes();
	SelectedDateRange.set(undefined);
	const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
	search_bar_input.value = '';
	SelectedSearchQuery.set('');
	SelectedClusters.set([]);
	isSelectionActive.set(false)
}

/**
 * Gets all the selected Node objects.
 * @return An array of selected Node objects.
 * @todo very slow for 5M Nodes, need another way.
 */

export function getSelectedNodes(): Node[] {
	return get(selectedNodes);
}

export function isSelectedNode(node: Node): boolean {
	const current = getSelectedNodes();

	// Rebuild the set only if the selection changed
	if (current !== lastSelected) {
		cachedIds = new Set(current.map((n) => n.id));
		lastSelected = current;
	}

	return cachedIds.has(node.id);
}

export function getClusterNodes() {
	return get(allClusterNodes);
}

export function getRenderedNodes() {
	return get(nodes);
}

export function setSelectedNodes(nodes: Node[]) {
	selectedNodes.set(nodes);
	graph.selectNodes(get(selectedNodes));
	isSelectionActive.set(true)
	//graph.addNodesFilter()
}

export function setSelectedNodesOnGraph(nodes: Node[]) {
	graph.selectNodes(nodes);
	isSelectionActive.set(true)
}

export function updateSelectedNodes(thenodes: Node[]) {
	selectedNodes.update((existingNodes) => {
		const existingIds = new Set(existingNodes.map((n) => n.id));

		const uniqueNewNodes = thenodes.filter((newNode) => !existingIds.has(newNode.id));

		return [...existingNodes, ...uniqueNewNodes];
	});
	graph.selectNodes(getSelectedNodes());
}

export function conditionalSelectNodes(theNodes: Node[]) {
	// get the matches
	const newNodes = new Set(theNodes.map((n) => n.id));
	const nodesToShowonGraph = getSelectedNodes().filter((n) => newNodes.has(n.id));
	setSelectedNodes(nodesToShowonGraph);
}

export function fitViewofGraph() {
	graph.fitView();
}

function showLabelsfor(nodes: Node[]) {
	if (nodes) {
		GraphConfig.showLabelsFor = nodes;
		updateGraphConfig(GraphConfig);
	} else {
		GraphConfig.showLabelsFor = undefined;
		updateGraphConfig(GraphConfig);
	}
}

// export function isSelectionActive(): boolean {
// 	return get(selectedNodesCount) !== 0;
// }

// export let isSelectionActive = derived(selectedNodesCount, ($count) => $count !== 0);
isSelectionActive.subscribe((active) => {
	// console.log(`isSelectionActive?: ${active}`)
	if(!active) selectedNodesCount.set(0)
})

export function getClusterNodesByClusterIds(cluster_ids: string[]): Node[] {
	const ClusterNodeIds = new Set(cluster_ids);
	const filteredNodes = getRenderedNodes().filter(
		(node) => ClusterNodeIds.has(node.id) && node.isClusterNode
	);
	return filteredNodes;
}
