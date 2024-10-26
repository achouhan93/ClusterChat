// Cosmograph Imports
import type {
	CosmographInputConfig,
	CosmographTimelineInputConfig
} from '@cosmograph/cosmograph';

import { type CosmosInputNode, type CosmosInputLink } from '@cosmograph/cosmos';
import { Cosmograph, CosmographTimeline } from '@cosmograph/cosmograph';
import { nodes, links, load10k, loadLables, getNodeColor, ClustersTree, getAssociatedLeafs, LoadAndSelect } from './readcluster';

// Other 
import '../app.css';
import type { Node, Link, Cluster } from '$lib/types';
import { DragSelect } from '$lib/components/graph/DragSelect';
import { get, writable } from 'svelte/store';
import { dragSelection } from './components/graph/D3DragSelection';

// Useful global variables
let graph: Cosmograph<Node, Link>;
let timeline: CosmographTimeline<Node>;

const BATCH_SIZE:number = 10000;
const MAX_SIZE:number = 100000;
const BATCH_NUMBER_START:number = 5
const INITIAL_BATCH_SIZE: number = BATCH_NUMBER_START*BATCH_SIZE;
let $batch_number= writable<number>(BATCH_NUMBER_START);
let $update_number=writable<number>(1);
export const INITIAL_FITVIEW:[[number,number],[number,number]] = [[10.784323692321777,21.064863204956055],[12.669471740722656,15.152010917663574]];
export let selectedNodes = writable<Node[]>([]);

export let selectMultipleNodes: boolean = false;
export let selectNodeRange: boolean = false;
let drag_select: boolean = false;
let hoveredNodeId = writable<string>("")

export let selectionArea: D3DragSelection | null=null;

/* ====================================== Graph and Timeline Event Handlers ====================================== */

const handleNodeClick = async (clickedNode: Node) => {
	if (!selectMultipleNodes && clickedNode) {
		showLabelsfor([clickedNode] as Node[]);
		graph.focusNode(clickedNode);
		graph.selectNode(clickedNode);
		setSelectedNodes([clickedNode])
	} else if (selectMultipleNodes && clickedNode) {
		selectedNodes.update((existingNodes)=>{return [...existingNodes, clickedNode]})
		graph.selectNodes(get(selectedNodes));
		showLabelsfor(get(selectedNodes));
	} else if (!clickedNode) {
		unselectNodes();
	}
};

const handleZoomEvent = async () => {
	const from_value:number = get($batch_number)*BATCH_SIZE
	console.log(`Current batch_number = ${get($batch_number)}`)
	console.log(`Current from_value = ${from_value}`)
		if(from_value < MAX_SIZE){
			// const current = get($BATCH_SIZE); 
			await load10k(from_value, BATCH_SIZE); // Await loading 10k nodes
			// $counter.update(currentValue => currentValue + 5000); 
			$batch_number.update(n => n+1);
			const nodenumber:number = get(nodes).length
			if(Math.floor(nodenumber/35000) > get($update_number)){
				updateGraphData();
				$update_number.update(n => n+1);
			}
		}
}

const handleLabelClick = async (node:Node) => {
	if(node.isClusterNode){
		const cluster_ids:string[] = getAssociatedLeafs(node.id)
		LoadAndSelect(cluster_ids)
		//updateSelectedNodes([node])		
	}
}
const handleTimelineSelection = async(selection:[Date,Date]) => {

	const nodesToSelect:Node[]=getRenderedNodes().filter(node => 
		node.date != undefined && new Date(node.date) >= selection[0] && new Date(node.date) <= selection[1])
		console.log(nodesToSelect)
	updateSelectedNodes(nodesToSelect)
}

/* ====================================== Config for the Graph and Timeline ====================================== */

export const GraphConfig: CosmographInputConfig<Node, Link> = {
	//backgroundColor: '#151515',
	backgroundColor: '#ffffff',
	//showFPSMonitor: true, /* shows performance monitor on the top right */
	nodeSize: (node: Node) => 0.01,
	nodeColor: (node: Node) => node.color,
	nodeLabelAccessor: (node: Node) => node.title,
	nodeLabelClassName: (node: Node) => node.isClusterNode ? 'cosmograph-cluster-label' : 'cosmograph-node-label',
	nodeLabelColor: (node:Node) => node.isClusterNode ? getNodeColor(node.x,node.y,INITIAL_FITVIEW,1) : "#fff",
	hoveredNodeLabelColor: (node:Node) => node.isClusterNode? '#000': node.color,
	hoveredNodeLabelClassName: 'cosmograph-hovered-node-label',
	hoveredNodeRingColor: '#2463EB',
	disableSimulation: true,
	renderLinks: false,
	scaleNodesOnZoom: true,
	fitViewByNodesInRect:INITIAL_FITVIEW,
	showDynamicLabels: false,
	showHoveredNodeLabel: false,
	showTopLabels: true,
	showTopLabelsLimit: 10,
	showTopLabelsValueKey: "isClusterNode",

	
	// Selection Event handled with button Click
	onClick(clickedNode) {handleNodeClick(clickedNode as Node);},
	onLabelClick(node) {
		handleLabelClick(node)
		showLabelsfor([node])
	},
	  // Scale node on hover
	  onNodeMouseOver(hoveredNode) {
		hoveredNodeId.set(hoveredNode.id);  // Track the hovered node by ID
		GraphConfig.nodeSize = (node: Node) => (node.id === get(hoveredNodeId) ? 0.1 : 0.01)
		updateGraphConfig(GraphConfig);  // Update the graph configuration to reflect the new node size
	  },
	  
	  // Reset node size when mouse leaves the node
	  onNodeMouseOut() {
		hoveredNodeId.set("")  // Reset the hovered node
		GraphConfig.nodeSize = (node: Node) => (node.id === get(hoveredNodeId) ? 0.1 : 0.01)
		updateGraphConfig(GraphConfig);  // Update the graph configuration to reset the node size
	  },
	// onZoom(){console.log(graph.getZoomLevel())},
	onMouseMove() {
		if (drag_select) {
			const container = document.getElementById('main-frame');
			const containerCanvas = container?.querySelector('canvas') as HTMLCanvasElement;

			if (containerCanvas) {
				selectionArea = new DragSelect(containerCanvas)
			}
		}
	},
	onZoomStart(e, userDriven){
		const ZoomLevel:number = graph.getZoomLevel() || 10
		if (ZoomLevel < 200){
			GraphConfig.showTopLabelsLimit = 10
		} else if(ZoomLevel > 200 && ZoomLevel < 1000) {
			GraphConfig.showTopLabelsLimit = Math.floor(ZoomLevel / 5)
		} else if (ZoomLevel > 1000) {
			GraphConfig.showTopLabelsLimit = 360
		}
		updateGraphConfig(GraphConfig)
		
		if(userDriven && e.sourceEvent.type != "mousedown"){		
			handleZoomEvent()
		}
	},
	onNodesFiltered(filteredNodes) {
		// console.log("Filtered Nodes: ")
		// console.log(filteredNodes)
	},

};

const TimelineConfig: CosmographTimelineInputConfig<Node> = {
	accessor: (d) => (d.date ? new Date(d.date) : 1 / 1 / 1970),
	allowSelection: true,
	showAnimationControls: true,
	dataStep:  1000*3600*24, 
	tickStep: 31557600000 / 12,  // One year in milliseconds,
	//axisTickHeight: 30,
	filterType: "nodes",
	formatter(d) {
		return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
	},
	onSelection(selection, isManuallySelected) {
		if(selection){
			handleTimelineSelection(selection)
		}
	},


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
	timeline = new CosmographTimeline<Node>(graph as unknown as Cosmograph<CosmosInputNode, CosmosInputLink>, 
		timelineContainer);
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
		main_frame.draggable = true;
		unselectNodes();
	}
}

/* ====================================== Graph Methods ====================================== */

async function initializeGraph(){
	await loadLables()
	await load10k(0,INITIAL_BATCH_SIZE)
	graph.setData(get(nodes),get(links))
}

export function updateGraphConfig(config: CosmographInputConfig<Node, Link>) {
	graph.setConfig(config);
}

export function updateGraphData(){
	const startTime = new Date().getTime()
	console.log("Updating the graph")
	nodes.subscribe(nodesArray => {
		graph.setData(nodesArray, get(links)); 
	});	
	const endTime = new Date().getTime()
	const duration = (Math.round(endTime - startTime)/1000)
	console.log(`Time to set Data: ${duration} sec`)
}

export function updateNodes(newNodes:Node[]){
	nodes.update(existingNodes => {
		// Append new nodes to the existing ones
		return [...existingNodes, ...newNodes];
	  });
}


export function selectNodesInRange(arr: [[number, number], [number, number]]) {
	// TODO: fix this function
	graph.selectNodesInRange(arr);
	selectedNodes.set(getSelectedNodes() as Node[])
}

export function unselectNodes() {
	graph.unselectNodes();
	showLabelsfor([]);
	selectedNodes.set([]);
}

export function getSelectedNodes() {
	return get(selectedNodes)
	// return graph.getSelectedNodes();
	
}

export function getRenderedNodes(){
	return get(nodes)
}

export function setSelectedNodes(nodes:Node[]){
	
	selectedNodes.set(nodes)
	graph.selectNodes(get(selectedNodes))
	//graph.addNodesFilter()
}

export function updateSelectedNodes(nodes:Node[]){
	selectedNodes.update(existingSelectedNodes => {
		return [...existingSelectedNodes, ...nodes]
	})
	graph.selectNodes(get(selectedNodes))
}


export function fitViewofGraph(){
	graph.fitView()
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


// Graph filters

function applyDateFilter(startDate: Date, endDate: Date) {
	const dateFilter = graph.addNodesFilter();
	console.dir(dateFilter)
	dateFilter.setAccessor((node) => node.isClusterNode && node.date ? 
	new Date(node.date).getTime(): new Date("2024-01-01").getTime());
	const startTimestamp = startDate.getTime();
	const endTimestamp = endDate.getTime();
	dateFilter.applyFilter((d) => d != undefined && d as number >= startTimestamp  && d as number <= endTimestamp);
	
}

	

// const SearchConfig: CosmographSearchInputConfig<Node> = {
// 	accessors: [
// 		{ label: 'ID', accessor: (node: Node) => node.id }
// 		// one for the abstracts
// 	],
// 	placeholder: 'Find documents...',
// 	ordering: {
// 		order: ['ID'],
// 		include: ['ID']
// 	},
// 	maxVisibleItems: 10,
// 	onSelectResult(clickedNode) {
// 		handleNodeClick(clickedNode as Node);
// 	},
// 	onSearch(foundMatches) {
// 		showLabelsfor(foundMatches as Node[]);
// 	},
// 	onEnter(input, accessor) {
// 		showLabelsfor([])
// 	},
// };

// export function createSearchBar() {
// 	const searchContainer = document.getElementById('main-search-bar') as HTMLDivElement;
// 	const search = new CosmographSearch<Node, Link>(graph, searchContainer);
// 	search.setConfig(SearchConfig);
// }
