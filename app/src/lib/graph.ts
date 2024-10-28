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
//import { DragSelect } from '$lib/components/graph/DragSelect';
// import { dragSelection } from './components/graph/D3DragSelection';
import { get, writable } from 'svelte/store';


// Useful global variables
let graph: Cosmograph<Node, Link>;
let timeline: CosmographTimeline<Node>;

const BATCH_SIZE:number = 10000; 
const MAX_SIZE:number = 100000; // TODO: make this dynamic
const BATCH_NUMBER_START:number = 5
const INITIAL_BATCH_SIZE: number = BATCH_NUMBER_START*BATCH_SIZE;
const HOVERED_NODE_SIZE:number = 0.5
let $batch_number= writable<number>(BATCH_NUMBER_START);
let $update_number=writable<number>(1);
export const INITIAL_FITVIEW:[[number,number],[number,number]] = [[10.784323692321777,21.064863204956055],[12.669471740722656,15.152010917663574]];
export let selectedNodes = writable<Node[]>([]);

export let SelectedDateRange = writable<[Date,Date]>(undefined);
export let SelectedSearchQuery = writable<string>('');
export let SelectedCluster = writable<string>('');

export let selectMultipleClusters= writable<boolean>(false); // TODO: change to multiple Cluster selection
export let selectNodeRange: boolean = false;

//let drag_select: boolean = false;
let hoveredNodeId = writable<string>("")


/* ====================================== Graph and Timeline Event Handlers ====================================== */

const handleNodeClick = async (clickedNode: Node) => {
	if (clickedNode && !isFilteringActive()) {
		showLabelsfor([clickedNode] as Node[]);
		graph.selectNode(clickedNode);
		setSelectedNodes([clickedNode])
	}  else if (!clickedNode) {
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
		SelectedCluster.set(node.id)
		console.log(get(SelectedCluster))
		const cluster_ids:string[] = getAssociatedLeafs(node.id)
		LoadAndSelect(cluster_ids)
	}
}
const handleTimelineSelection = async(selection:[Date,Date] | [number,number]) => {
	
	if(getRenderedNodes().length !=0){
		if(selection.length === 2 && selection[0] instanceof Date && selection[1] instanceof Date){SelectedDateRange.set(selection)}
		// TODO: update range also from opensearch
		const nodesToSelect:Node[]=getRenderedNodes().filter(node => 
			node.date != undefined && new Date(node.date) >= selection[0] && new Date(node.date) <= selection[1])
			
		if (getSelectedNodes().length == 0)	{

			setSelectedNodes(nodesToSelect)
		}
		else {
			conditionalSelectNodes(nodesToSelect)
		 } // TODO: conditional selection

		// TODO: for some reason the graph selection only appears,
		// when the user clicks outside the blue timeline selection box!
		// so setting the selection to [0,0] emulates that
		timeline.setSelection([0,0])
	}

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
	initialZoomLevel: 100,
	scaleNodesOnZoom: true,
	// fitViewByNodesInRect:INITIAL_FITVIEW,
	showDynamicLabels: false,
	showHoveredNodeLabel: false,
	showTopLabels: true,
	showTopLabelsLimit: 10,
	showTopLabelsValueKey: "isClusterNode",

	
	// Selection Event handled with button Click
	onClick(clickedNode) {handleNodeClick(clickedNode as Node);},
	onLabelClick(node) {
		handleLabelClick(node)
	},
	  // Scale node on hover
	  onNodeMouseOver(hoveredNode) {
		hoveredNodeId.set(hoveredNode.id);  // Track the hovered node by ID
		const main_frame = document.getElementById('main-graph');
		main_frame.style.cursor = "pointer"
		GraphConfig.nodeSize = (node: Node) => (node.id === get(hoveredNodeId) ? HOVERED_NODE_SIZE : 0.01)

		updateGraphConfig(GraphConfig);  // Update the graph configuration to reflect the new node size
	  },
	  
	  // Reset node size when mouse leaves the node
	  onNodeMouseOut() {
		hoveredNodeId.set("")  // Reset the hovered node
		GraphConfig.nodeSize = (node: Node) => (node.id === get(hoveredNodeId) ? HOVERED_NODE_SIZE : 0.01)
		updateGraphConfig(GraphConfig);  // Update the graph configuration to reset the node size
		const main_frame = document.getElementById('main-graph');
		main_frame.style.cursor = "default"
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
		
/* 		if(userDriven && e.sourceEvent.type != "mousedown"){		
			handleZoomEvent()
		} */
	},
	onNodesFiltered(filteredNodes) {
		console.log("Filtered Nodes: ")
		console.log(filteredNodes)
	},

};

const TimelineConfig: CosmographTimelineInputConfig<Node> = {
	accessor: (d) => (d.date ? new Date(d.date) : new Date("2024-01-01")),
	dataStep:  1000*3600*24, 
	tickStep: 31557600000 / 12,  // One year in milliseconds,
	//axisTickHeight: 30,
	filterType: "nodes",
	formatter(d) {
		return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
	},
	onSelection(selection) {
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
export function toggleMultipleClustersMode() {
	selectMultipleNodes.update((value) => !value);
	selectNodeRange = false;
}

// export function toggleSelectNodeRange() {
// 	selectNodeRange = !selectNodeRange;
// }
// export function toggleDragSelection() {
// 	drag_select = !drag_select;
// 	const main_frame = document.getElementById('main-graph');
// 	if (drag_select) {
// 		main_frame.style.cursor = 'crosshair';
// 	} else {
// 		main_frame.style.cursor = 'default';
// 		unselectNodes();
// 	}
// }

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
	// make sure you update only unique
	nodes.update(existingNodes => {
		const existingIds = new Set(existingNodes.map(node => node.id));
	
		const uniqueNewNodes = newNodes.filter(newNode => !existingIds.has(newNode.id));
	
		return [...existingNodes, ...uniqueNewNodes];
	});
}


export function selectNodesInRange(arr: [[number, number], [number, number]]) {
	// TODO: fix this function
	graph.selectNodesInRange(arr);
	selectedNodes.set(getSelectedNodes() as Node[])
}

export function unselectNodes() {
	selectedNodes.set([]);
	graph.unselectNodes();
	showLabelsfor([])
	SelectedDateRange.set(undefined)
	SelectedSearchQuery.set("")
	SelectedCluster.set("")
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

export function updateSelectedNodes(thenodes:Node[]){
	selectedNodes.update(existingNodes => {
		const existingIds = new Set(existingNodes.map(node => node.id));
	
		const uniqueNewNodes = thenodes.filter(newNode => !existingIds.has(newNode.id));
	
		return [...existingNodes, ...uniqueNewNodes];
	});
	graph.selectNodes(getSelectedNodes())
	
}

export function conditionalSelectNodes(theNodes:Node[]){
	// get the matches
	const newNodes = new Set(theNodes.map(node => node.id))
	const nodesToShowonGraph = getSelectedNodes().filter(node => newNodes.has(node.id))
	setSelectedNodes(nodesToShowonGraph)
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

export function isFilteringActive():boolean{
	if (get(SelectedDateRange) != undefined || get(SelectedSearchQuery) != "" ||
	get(SelectedCluster) != "" ) return true
	return false
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
