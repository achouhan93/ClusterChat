// Cosmograph Imports
import type {
	CosmographInputConfig,
	CosmographTimelineInputConfig
} from '@cosmograph/cosmograph';

import { type CosmosInputNode, type CosmosInputLink } from '@cosmograph/cosmos';
import { Cosmograph, CosmographTimeline } from '@cosmograph/cosmograph';
import { nodes, links, load10k, loadLables, getNodeColor, getAssociatedLeafs, LoadNodesByCluster, allClusters, allClusterNodes, ClustersTree } from './readcluster';


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
const BATCH_NUMBER_START:number = 3;// TO CHANGE BEFORE PUSH
const INITIAL_BATCH_SIZE: number = BATCH_NUMBER_START*BATCH_SIZE;
const HOVERED_NODE_SIZE:number = 0.5
// let $batch_number= writable<number>(BATCH_NUMBER_START);
// let $update_number=writable<number>(1);
export const INITIAL_FITVIEW:[[number,number],[number,number]] = [[10.784323692321777,21.064863204956055],[12.669471740722656,15.152010917663574]];
export let selectedNodes = writable<Node[]>([]);

export let SelectedDateRange = writable<[Date,Date]>(undefined);
export let SelectedSearchQuery = writable<string>('');
export let SelectedCluster = writable<string>([]);

export let selectMultipleClusters= writable<boolean>(false); // TODO: change to multiple Cluster selection
export let hierarchicalLabels = writable<boolean>(false);
export let selectNodeRange: boolean = false;

//let drag_select: boolean = false;
let hoveredNodeId = writable<string>("")
export let hNode = writable<Node>();
export let document_specific = writable(true);

/* ====================================== Graph and Timeline Event Handlers ====================================== */

const handleNodeClick = async (clickedNode: Node) => {
	if (clickedNode && !isFilteringActive() && get(document_specific)) {
		showLabelsfor([clickedNode] as Node[]);
		graph.selectNode(clickedNode);
		setSelectedNodes([clickedNode])
	}  else if (!clickedNode) {
		unselectNodes();
	}
};

const handleZoomEvent = async () => {
	// TODO: change all!!
	/* const from_value:number = get($batch_number)*BATCH_SIZE
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
		} */
}

const handleLabelClick = async (node:Node) => {
	if(node.isClusterNode){
		SelectedCluster.set(node.id)
		console.log(`Selected Cluster Id: ${node.id}`)
		const cluster_ids:string[] = getAssociatedLeafs(node.id,node.title)
		console.log(cluster_ids)
		LoadNodesByCluster(cluster_ids)

		// get all the rendered nodes and filter the ones that have the cluster ids
		const set_cluster_ids = new Set(cluster_ids);
		const filteredNodes =  getRenderedNodes().filter(node => set_cluster_ids.has(node.cluster))
		
		if (getSelectedNodes().length == 0){
			selectedNodes.set(filteredNodes)
			filteredNodes.push(node)
			graph.selectNodes(filteredNodes)
		} else {
			const filteredNodesSet = new Set(filteredNodes.map(node => node.id))
			const nodesToShowonGraph = getSelectedNodes().filter(node => filteredNodesSet.has(node.id))
			selectedNodes.set(nodesToShowonGraph)
			nodesToShowonGraph.push(node)
			graph.selectNodes(nodesToShowonGraph)
		}
	}
}
const handleTimelineSelection = async(selection:[Date,Date] | [number,number]) => {
	
	if(getRenderedNodes().length !=0){
		if(selection.length === 2 && selection[0] instanceof Date && selection[1] instanceof Date){SelectedDateRange.set(selection)}

		const nodesToSelect:Node[]=getRenderedNodes().filter(node => 
			node.date != undefined && new Date(node.date) >= selection[0] && new Date(node.date) <= selection[1])
			
		if (getSelectedNodes().length == 0)	{

			//setSelectedNodes(nodesToSelect)
			selectedNodes.set(nodesToSelect)
			const graphNodesToSelect = nodesToSelect.concat(get(allClusterNodes))
			graph.selectNodes(graphNodesToSelect)
		}
		else {
			// TODO
			const nodesToSelectSet = new Set(nodesToSelect.map(node => node.id))
			const nodesToShowonGraph = getSelectedNodes().filter(node => nodesToSelectSet.has(node.id))
			selectedNodes.set(nodesToShowonGraph)
			const graphNodesToSelect = nodesToShowonGraph.concat(get(allClusterNodes))
			graph.selectNodes(graphNodesToSelect)
		 } 

		// TODO: for some reason the graph selection only appears,
		// when the user clicks outside the blue timeline selection box!
		// so setting the selection to [0,0] emulates that
		timeline.setSelection([0,0])
	}

}

const handleOnZoomStartHierarchical = async () => {
		const ZoomLevel:number = graph.getZoomLevel() || 10
		let ClusterLabelsToShow:string[]=[]
		if (ZoomLevel < 30){
			ClusterLabelsToShow =  [7,8].map(index => get(ClustersTree)[index]).flat();
		}
		else if (ZoomLevel > 30 && ZoomLevel < 150){
			ClusterLabelsToShow =  [6,7].map(index => get(ClustersTree)[index]).flat();
		} else if(ZoomLevel > 150 && ZoomLevel < 200) {
			ClusterLabelsToShow =  [4,5,6,7].map(index => get(ClustersTree)[index]).flat();
		} else if (ZoomLevel > 200 && ZoomLevel < 600) {
			ClusterLabelsToShow =  [3,4,5,6].map(index => get(ClustersTree)[index]).flat();	
		} else if (ZoomLevel > 600) {
			ClusterLabelsToShow =  [0,1,2,3,4,5,6].map(index => get(ClustersTree)[index]).flat();	
		}
		GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow)
		updateGraphConfig(GraphConfig)
		console.log(ZoomLevel)
}

const handleOnZoomStartTopLabel = () => {
	const ZoomLevel:number = graph.getZoomLevel() || 10
	let ClusterLabelsToShow:string[]=[]
	if (ZoomLevel < 200){
		GraphConfig.showTopLabelsLimit = 6
	} else if(ZoomLevel > 200 && ZoomLevel < 600) {
		GraphConfig.showTopLabelsLimit = Math.floor(ZoomLevel /10)
	} else if (ZoomLevel > 600) {
		GraphConfig.showTopLabelsLimit = get(allClusters).length	
	}
	GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow)
	updateGraphConfig(GraphConfig)
	console.log(ZoomLevel)
}

/* ====================================== Config for the Graph and Timeline ====================================== */

export const GraphConfig: CosmographInputConfig<Node, Link> = {
	//backgroundColor: '#151515',
	backgroundColor: '#ffffff',
	nodeGreyoutOpacity: 0.01,
	//showFPSMonitor: true, /* shows performance monitor on the top right */
	nodeSize: (node: Node) => 0.01,
	nodeColor: (node: Node) => node.color,
	nodeLabelAccessor: (node: Node) => node.title,
	//nodeLabelClassName: (node: Node) => node.isClusterNode ? `cosmograph-cluster-label-${node.date}` : 'cosmograph-node-label', // getNodeLabelClassName
	nodeLabelClassName: (node:Node) => node.isClusterNode ? 'cosmograph-cluster-label' : 'cosmograph-node-label',
	nodeLabelColor: (node:Node) => node.isClusterNode? getNodeColor(node.x,node.y,INITIAL_FITVIEW,1) : '#fff',
	// nodeLabelColor: (node:Node) => node.isClusterNode ? '#808080' : "#fff",
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
	},
	  // Scale node on hover
	  onNodeMouseOver(hoveredNode) {
		if(hoveredNode){
			hNode.set(hoveredNode)
			hoveredNodeId.set(hoveredNode.id);  // Track the hovered node by ID
			const main_frame = document.getElementById('main-graph');
			main_frame.style.cursor = "pointer"
			GraphConfig.nodeSize = (node: Node) => (node.id === get(hoveredNodeId) ? HOVERED_NODE_SIZE : 0.01)
			updateGraphConfig(GraphConfig);  // Update the graph configuration to reflect the new node size
		} 
	  },
	  
	  // Reset node size when mouse leaves the node
	  onNodeMouseOut() {
		hoveredNodeId.set("")  // Reset the hovered node
		hNode.set(undefined)
		if(get(hNode) === undefined) console.log("Node Not Hovered")
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

		// const ZoomLevel:number = graph.getZoomLevel() || 10
		// let ClusterLabelsToShow:string[]=[]
		// if (ZoomLevel < 150){
		// 	ClusterLabelsToShow =  [4,5,6,7].map(index => get(ClustersTree)[index]).flat();
		// } else if(ZoomLevel > 150 && ZoomLevel < 250) {
		// 	ClusterLabelsToShow =  [5,6,7].map(index => get(ClustersTree)[index]).flat();
		// } else if (ZoomLevel > 250 && ZoomLevel < 600) {
		// 	ClusterLabelsToShow =  [3,4,5].map(index => get(ClustersTree)[index]).flat();	
		// } else if (ZoomLevel > 600) {
		// 	ClusterLabelsToShow =  [1,2,3].map(index => get(ClustersTree)[index]).flat();	
		// }
		// GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow)
		// updateGraphConfig(GraphConfig)
		// console.log(ZoomLevel)


		const ZoomLevel:number = graph.getZoomLevel() || 10
		let ClusterLabelsToShow:string[]=[]
		if (ZoomLevel < 200){
			GraphConfig.showTopLabelsLimit = 6
		} else if(ZoomLevel > 200 && ZoomLevel < 600) {
			GraphConfig.showTopLabelsLimit = Math.floor(ZoomLevel /10)
		} else if (ZoomLevel > 600) {
			GraphConfig.showTopLabelsLimit = get(allClusters).length	
		}
		GraphConfig.showLabelsFor = getClusterNodesByClusterIds(ClusterLabelsToShow)
		updateGraphConfig(GraphConfig)
		console.log(ZoomLevel)
		
		// change all
/* 		if(userDriven && e.sourceEvent.type != "mousedown"){		
			handleZoomEvent()
		} */
	},
	onNodesFiltered(filteredNodes) {
		// console.log("Filtered Nodes: ")
		// console.log(filteredNodes)
	},

};

const TimelineConfig: CosmographTimelineInputConfig<Node> = {
	accessor: (d) => (d.date ? new Date(d.date) : new Date("2024-01-01")),
	dataStep:  1000*3600*12, 
	tickStep: 31557600000 / 12,  // One year in milliseconds,
	//axisTickHeight: 30,
	filterType: "nodes",
	formatter(d) {
		// TO CHANGE FOR 4M
		//return new Date(d).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
		return "";
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

	selectMultipleClusters.update((value) => !value);
	
}
export function toggleHierarchicalLabels(){
	if (get(hierarchicalLabels))
	{
		GraphConfig.showTopLabels = true
		GraphConfig.showLabelsFor = undefined
		GraphConfig.showTopLabelsLimit= 10
		GraphConfig.showTopLabelsValueKey = "isClusterNode"
		GraphConfig.nodeLabelClassName = (node:Node) => node.isClusterNode ? 'cosmograph-cluster-label' : 'cosmograph-node-label'
		GraphConfig.onZoom = handleOnZoomStartTopLabel
	}
	else {
		GraphConfig.showTopLabels = false
		GraphConfig.showTopLabelsLimit= undefined
		GraphConfig.showTopLabelsValueKey = undefined
		GraphConfig.nodeLabelClassName = (node: Node) => node.isClusterNode ? `cosmograph-cluster-label-${node.date}` : 'cosmograph-node-label'
		GraphConfig.onZoom = handleOnZoomStartHierarchical
	}
	updateGraphConfig(GraphConfig)
	hierarchicalLabels.update((value) => !value)
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
	SelectedDateRange.set(undefined)
	const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
	search_bar_input.value = '';
	SelectedSearchQuery.set('')
	SelectedCluster.set("")
}

export function getSelectedNodes() {
	return get(selectedNodes)
	// return graph.getSelectedNodes();

}

export function getClusterNodes(){
	return get(allClusterNodes)
}

export function getRenderedNodes(){
	return get(nodes)
}

export function setSelectedNodes(nodes:Node[]){
	
	selectedNodes.set(nodes)
	graph.selectNodes(get(selectedNodes))
	//graph.addNodesFilter()
}

export function setSelectedNodesOnGraph(nodes:Node[]){
	graph.selectNodes(nodes)
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

export function getClusterNodesByClusterIds(cluster_ids:string[]):Node[]{
	const ClusterNodeIds = new Set(cluster_ids)
	const filteredNodes =  getRenderedNodes().filter(node => ClusterNodeIds.has(node.id) && node.isClusterNode)
	return filteredNodes
}


