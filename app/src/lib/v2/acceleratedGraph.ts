// Cosmograph Imports
import type {
	CosmographConfig,
	CosmographTimelineConfig,
	CosmographDataPrepConfig,
	CosmographData
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
	selectNodeRange,
	isSelectionActive,
	selectedPointsIds,
	numberOfSelectedPoints
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
export let graph: Cosmograph;
// export let graph = writable<Cosmograph>
let timeline: CosmographTimeline

/* ====================================== Graph and Timeline Event Handlers ====================================== */
isSelectionActive.subscribe((active) => {
    console.log(`isSelectionActive?: ${active}`)
	if(!active) numberOfSelectedPoints.set(0)
})
// numberOfSelectedPoints.subscribe()

//     pageCount.set(active ? get(numberOfSelectedPoints) : 0);
// 	console.log(`pageCount: ${get(pageCount)}`)

const handlePointClick = async (index:number) => {
    if (index && !get(isSelectionActive) && get(document_specific)) {
        setSelectPoint(index)
    }
};
const handlePointsFiltered = async (table: CosmographData) => {
		numberOfSelectedPoints.set(table.numRows)
        isSelectionActive.set(true)
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
    pointGreyoutOpacity: 0.02,
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
    onClick(pointIndex) {
        if(pointIndex){ 
            handlePointClick(pointIndex) 
            outputLog(pointIndex)
        } else {
            unselectAllPoints()
        }
        
        
    },
    onPointMouseOver(hoveredPointIndex) {
        if(!get(isSelectionActive)){

        }
    },
    // very useful for date selection
    onPointsFiltered(SelectedPointsTable) {
		console.log(`onPointsFiltered: ${SelectedPointsTable.numRows}`)
        handlePointsFiltered(SelectedPointsTable)	
    },
    onGraphRebuilt(stats){
        console.log(`Stats of the Graph: ${stats}`)
    }



} 

const TimelineConfig: CosmographTimelineConfig = {
	accessor: 'date',
	barRadius: 3,
	barPadding: 0.5,
	tickStep: 15_778_560_000, // approx. 6 months
	// dataStep: 2_629_743_590,  // approx. 1 month

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

export function getSelectedPointIndices() {
	const indices = graph.getSelectedPointIndices() 
	if (indices) return indices
	return null
}

export function getSelectedPointCount() {
	return get(numberOfSelectedPoints) || 0
}

export function setSelectPoint(index:number) {
	graph.selectPoint(index)
	isSelectionActive.set(true)
}
export function setSelectPoints(indices:number[]) {
	graph.selectPoints(indices)
	console.log(`setSelectPoints after .selectPoints: ${get(numberOfSelectedPoints)}`)
}
export const setArrayofSelectedPointIds = async (indices: number[]) => {
	const pointIds = await graph.getPointIdsByIndices(indices) || []
	selectedPointsIds.set(pointIds)
}


export function unselectAllPoints() {
	graph.unselectAllPoints()
	isSelectionActive.set(false)
	selectedPointsIds.set([])
}

export function unselectPoint() {
	graph.unselectPoint()
	if(get(numberOfSelectedPoints) === 0) { //getSelectedPointCount() === 0
		isSelectionActive.set(false)
	}
}

export async function getPointIndicesByIds(ids:string[]){
	return await graph.getPointIndicesByIds(ids)
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
