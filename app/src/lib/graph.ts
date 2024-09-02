/*
- cosmograph timeline
- cosmograph filtration by cluster
- cosmograph search


pubmed_id (use for the references with https://pubmed.ncbi.nlm.nih.gov/)
title
articleDate
doi
be as generic with the namings as possible
Clusters to use:
-----------------------------------------------
frameintell_arxiv_*
frameintell_arxiv_embeddings (Embeddings: 2.4M)
*/

/* TODO


* Area Selection with drag feature
* add events to the search bar (Zooming doesn't work as intendet)
* add chat feature
*/

/* DONE 

* Add multiple selection
* add search bar 
* add timeline
*/

/* Suggestions
* include scales for customization

*/

// Cosmograph Imports
import type {
	CosmographInputConfig,
	CosmographSearchInputConfig,
	CosmographTimelineInputConfig
} from '@cosmograph/cosmograph';
import { type CosmosInputNode, type CosmosInputLink } from '@cosmograph/cosmos';
import { Cosmograph, CosmographSearch, CosmographTimeline } from '@cosmograph/cosmograph';
import { nodes, links, getNodesfromOpenSearch } from './readcluster';

// Other 
import '../app.css';
import type { Node, Link } from '$lib/types';
import { DragSelect } from '$lib/components/graph/DragSelect';

// Useful global variables
let graph: Cosmograph<Node, Link>;
let timeline: CosmographTimeline<Node>;
export let selectMultipleNodes: boolean = false;
export let selectNodeRange: boolean = false;
let drag_select: boolean = false;
let selectedNodes: Node[] = [];
export let selectionArea: DragSelect | null = null;


// Config for the Graph, Search and Timeline
export const GraphConfig: CosmographInputConfig<Node, Link> = {
	//backgroundColor: '#151515',
	backgroundColor: '#343a40',
	//showFPSMonitor: true, /* shows performance monitor on the top right */
	nodeSize: (node: Node) => node.size,
	nodeColor: (node: Node) => node.color,
	nodeLabelAccessor: (node: Node) => node.title,
	nodeLabelClassName: 'cosmograph-node-label',
	hoveredNodeLabelClassName: 'cosmograph-hovered-node-label',
	hoveredNodeRingColor: '#2463EB',
	showHoveredNodeLabel: true,
	showDynamicLabels: false,
	nodeGreyoutOpacity: 0.009,
	disableSimulation: true,
	renderLinks: false,
	//nodeLabelColor: '#FFFFFF',
	hoveredNodeLabelColor: '#FFFFFF',
	focusedNodeRingColor: 'yellow',
	// Selection Event handled with button Click
	onClick(clickedNode) {
		handleNodeClick(clickedNode as Node);
	},
	onLabelClick(node, event) {
		console.log(node.id);
	},
	onMouseMove() {
		if (drag_select) {
			const container = document.getElementById('main-frame');
			if (container && !selectionArea) {
				selectionArea = new DragSelect(container);
			}
		}
	}
};

const SearchConfig: CosmographSearchInputConfig<Node> = {
	accessors: [
		{ label: 'Title', accessor: (node: Node) => node.title }
		// one for the abstracts
	],
	placeholder: 'Find documents...',
	ordering: {
		order: ['Title'],
		include: ['Title']
	},
	maxVisibleItems: 10,
	onSelectResult(clickedNode) {
		handleNodeClick(clickedNode as Node);
	},
	onSearch(foundMatches) {
		showLabelsfor(foundMatches as Node[]);
	}
};

const TimelineConfig: CosmographTimelineInputConfig<Node> = {
	accessor: (d) => (d.date ? d.date : 12 / 12 / 2000),
	showAnimationControls: true,
	allowSelection: true
};


// create components
export function createGraph() {
	const canvas = document.getElementById('main-graph') as HTMLDivElement;
	graph = new Cosmograph(canvas, GraphConfig);
	graph.setConfig(GraphConfig);
	graph.setData(nodes, links);
}

export function createSearchBar() {
	const searchContainer = document.getElementById('main-search-bar') as HTMLDivElement;
	const search = new CosmographSearch<Node, Link>(graph, searchContainer);
	search.setConfig(SearchConfig);
}

export function createTimeline() {
	const timelineContainer = document.getElementById('main-timeline') as HTMLDivElement;
	const castedGraph = graph as unknown as Cosmograph<CosmosInputNode, CosmosInputLink>; // for typecasting
	timeline = new CosmographTimeline<Node>(castedGraph, timelineContainer);
	timeline.setConfig(TimelineConfig);
}

// control buttons functions
export function toggleMultipleNodesMode() {
	selectMultipleNodes = !selectMultipleNodes;
	selectNodeRange = false;
}

export function toggleSelectNodeRange() {
	selectNodeRange = !selectNodeRange;
}
export function toggleDragSelection() {
	drag_select = !drag_select;
	const main_frame = document.getElementById('main-graph');
	if (drag_select) {
		main_frame.style.cursor = 'crosshair';
	} else {
		main_frame.style.cursor = 'default';
		selectionArea?.destroy();
		selectionArea = null;
		unselectNodes();
	}
}

// Graph functionalities
export function updateGraph(config: CosmographInputConfig<Node, Link>) {
	graph.setConfig(config);
}

export function selectNodesInRange(arr: [[number, number], [number, number]]) {
	graph.selectNodesInRange(arr);
	selectedNodes = graph.getSelectedNodes() as Node[];
}

export function unselectNodes() {
	graph.unselectNodes();
	showLabelsfor([]);
	selectedNodes = [];
}

export function getSelectedNodes() {
	selectedNodes = graph.getSelectedNodes() as Node[];
	if (selectedNodes) {
		return selectedNodes;
	} else {
		selectedNodes = [];
		return selectedNodes;
	}
}

export function fitViewofGraph(){
	graph.fitView()
}

function showLabelsfor(nodes: Node[]) {
	if (nodes) {
		GraphConfig.showLabelsFor = nodes;
		updateGraph(GraphConfig);
	} else {
		GraphConfig.showLabelsFor = undefined;
		updateGraph(GraphConfig);
	}
}

const handleNodeClick = async (clickedNode: Node) => {
	if (!selectMultipleNodes && clickedNode) {
		showLabelsfor([clickedNode] as Node[]);
		graph.focusNode(clickedNode);
		graph.selectNode(clickedNode);
		selectedNodes = [clickedNode];
	} else if (selectMultipleNodes && clickedNode) {
		selectedNodes.push(clickedNode); // Add clicked node to selectedNodes
		graph.selectNodes(selectedNodes);
		showLabelsfor(selectedNodes);
	} else if (!clickedNode) {
		unselectNodes();
	}
};
