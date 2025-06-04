// Cosmograph Imports
import type {
	CosmographConfig,
	CosmographTimelineConfig,
	CosmographDataPrepConfig
} from 'cosmograph-v2';
import { Cosmograph, CosmographTimeline } from 'cosmograph-v2';


import {
	load10k,
	loadLables,
	getNodeColor,
	getAssociatedLeafs,
	LoadNodesByCluster
} from '../readcluster';

import {
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
	selectNodeRange,
	isSelectionActive,
	selectedPointsIds
} from '$lib/stores/nodeStore';

import { hierarchicalLabels, document_specific, pageCount } from '$lib/stores/uiStore';


// Other
import '../../app.css';
import type { Node, Link, Cluster, Point } from '$lib/types';
;
import { get, derived, writable } from 'svelte/store';
import { LabelsKeys, type CosmographPointInput } from 'cosmograph-v2/cosmograph/config';
import { page } from '$app/state';

// Useful global variables
let graph: Cosmograph;
let timeline: CosmographTimeline
const HOVERED_NODE_SIZE: number = 0.5;

/* ====================================== Graph and Timeline Event Handlers ====================================== */
isSelectionActive.subscribe((active) => {
    console.log(`isSelectionActive?: ${active}`)
    pageCount.set(active ? getSelectedPointsCount() : 0);
})

const handlePointClick = async (index:number) => {
    if (index && !get(isSelectionActive) && get(document_specific)) {
        setSelectPoint(index)
    }
};

const handlePointsFiltered = async () => {
        if (!get(isSelectionActive) && getSelectedPointsCount() !== 0) {
        isSelectionActive.set(true)
    }
}

// For logging REMOVE FOR PRODUCTION
const outputLog = async (index:number) => {
    console.log(await graph.getPointIdsByIndices([index]))
}
function outputLogIds (){
    const indices = graph.getSelectedPointIndices() ?? [1]
    // const pointIds = await graph.getPointIdsByIndices(indices)
    console.log(indices)

}
/* ====================================== Config for the Graph and Timeline ====================================== */
const GraphConfig: CosmographConfig = {
    backgroundColor: '#ffffff',
    pointGreyoutOpacity: 0.04,
    pointSize: 3, 
    // pointSizeByFn?,
    renderLinks: false,
    focusPointOnClick: true,
    fitViewOnInit: true,
    showDynamicLabels: false,
    showHoveredPointLabel: false,
    showTopLabels: true,
    showTopLabelsLimit: 10,
    showClusterLabels: true,
    hoveredPointLabelClassName: 'cosmograph-hovered-node-label',
    hoveredPointCursor: 'pointer',
	selectPointOnLabelClick: false,
  
    onPointMouseOver(hoveredPointIndex) {
        if(hoveredPointIndex && !get(isSelectionActive) && get(document_specific)){
			GraphConfig.pointSize = (hNode) => hNode === hoveredPointIndex ? HOVERED_NODE_SIZE : 0.04
        }
    },
    // very useful for date selection
    onPointsFiltered() {
        handlePointsFiltered()	
    },
    onGraphRebuilt(stats){
        console.log(`Stats of the Graph: ${stats}`)
    }



} 

const TimelineConfig: CosmographTimelineConfig = {
	accessor: 'date',
	barRadius: 3,
	barPadding: 0.5,

}

/* ====================================== Functions to Create Graph and Timeline ====================================== */



export async function createGraph(pointsPath:string, pointsConfigPath:string) {
	const points = await fetch(pointsPath).then(res => res.blob())
	const pointsConfig = await fetch(pointsConfigPath).then(res => res.json())
	const pointsFile = new File([points], 'cosmograph-points.arrow', { type: 'application/octet-stream' })
	const container: HTMLElement = document.getElementById('main-graph');
	const ConfigData: CosmographConfig = { 
		points: pointsFile, 
		...pointsConfig,
		...GraphConfig
	}
	graph = new Cosmograph(container, ConfigData)
}

export async function createTimeline() {
	const timelineContainer = document.getElementById('main-timeline') as HTMLDivElement;
	timeline = new CosmographTimeline(graph, timelineContainer, TimelineConfig)
}

// Alternative Way for createGraph
	// const arrowFile = await fetch("src/lib/data/cosmograph-points.arrow")
	// const points = await tableFromIPC(arrowFile)
	// console.table([...points]);
	// const config = await fetch("src/lib/data/cosmograph-config.json")
	// console.log(points)
	// console.log(config)
	// createGraph(points,config)

// export function createTimeline() {}

// control buttons functions
export function toggleMultipleClustersMode() {}
export function toggleHierarchicalLabels() {}

/* ====================================== Graph Methods ====================================== */


export function setGraphConfig(config: CosmographConfig) {
	graph.setConfig(config);
}


export function updateGraphData() {

}

export function selectPointsInRange(arr: [[number, number], [number, number]]) {
}


/**
 * Gets all the selected Point objects.
 * @return An array of selected Point objects.
 * @todo very slow for 5M Points, need another way.
 */

export function getSelectedPointsIndices() {
	return graph.getSelectedPointIndices() || []
}

export function getSelectedPointsCount() {
	return getSelectedPointsIndices()?.length || 0
}

export function setSelectPoint(index:number) {
	graph.selectPoint(index)
	isSelectionActive.set(true)
}
export const setSelectedPointsIds = async (indices: number[]) => {
	const pointIds = await graph.getPointIdsByIndices(indices) || []
	selectedPointsIds.set(pointIds)
}
export function setSelectPoints(indices:number[]) {
	graph.selectPoints(indices)
	isSelectionActive.set(true)
}

export function unselectAllPoints() {
	graph.unselectAllPoints()
	isSelectionActive.set(false)
	selectedPointsIds.set([])
}

export function unselectPoint() {
	graph.unselectPoint()
	if(getSelectedPointsCount() === 0) {
		isSelectionActive.set(false)
	}
	
}

export function isPointSelectedByIndex(): boolean {}

export function getClusterPoints() {
	// return get(allClusterPoints);
}

export function getRenderedPoints() {
	// return get(Points);
}

export function setSelectedPoints(Points: Point[]) {
	// selectedPoints.set(Points);
	// graph.selectPoints(get(selectedPoints));
	//graph.addPointsFilter()
}

export function setSelectedPointsOnGraph(Points: Point[]) {
	// graph.selectPoints(Points);
}

export function updateSelectedPoints(thePoints: Point[]) {}

export function conditionalSelectPoints(thePoints: Point[]) {
	// get the matches
	// const newPoints = new Set(thePoints.map((n) => n.id));
	// const PointsToShowonGraph = getSelectedPoints().filter((n) => newPoints.has(n.id));
	// setSelectedPoints(PointsToShowonGraph);
}

export function fitViewofGraph() {
	graph.fitView();
}

function showLabelsfor(Points: Point[]) {
	
	// if (Points) {
	//     GraphConfig.showLabelsFor = Points;
	//     updateGraphConfig(GraphConfig);
	// } else {
	//     GraphConfig.showLabelsFor = undefined;
	//     updateGraphConfig(GraphConfig);
	// }
}

// export function isSelectionActive(): boolean {
// 	return get(selectedPointsCount) !== 0;
// }

// export let isSelectionActive = derived(selectedPointsCount, ($count) => $count !== 0);



// export function isSelectionActive(): boolean {
// 	if (getSelectedPointsCount() as number > 0) return true
// 	return false
// }
export function getClusterPointsByClusterIds(cluster_ids: string[]): Point[] {
	// const ClusterPointIds = new Set(cluster_ids);
	// const filteredPoints = getRenderedPoints().filter(
	//     (Point) => ClusterPointIds.has(Point.id) && Point.isClusterPoint
	// );
	// return filteredPoints;
}
