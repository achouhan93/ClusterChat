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
	selectNodeRange
} from '$lib/stores/nodeStore';

import { hierarchicalLabels, document_specific } from '$lib/stores/uiStore';

// Other
import '../../app.css';
import type { Node, Link, Cluster, Point } from '$lib/types';
//import { DragSelect } from '$lib/components/graph/DragSelect';
// import { dragSelection } from './components/graph/D3DragSelection';
import { get, derived } from 'svelte/store';
import { LabelsKeys, type CosmographPointInput } from 'cosmograph-v2/cosmograph/config';

// Useful global variables
let graph: Cosmograph;
let timeline: CosmographTimeline

let cachedIds = new Set<string>();
let lastSelected = [];

/* ====================================== Graph and Timeline Event Handlers ====================================== */

const handlePointClick = async (index:number) => {
	if (index && !isSelectionActive() && get(document_specific)) {
		graph.selectPoint(index);
		console.log(index)
		//graph.showLabelsfor
	}
};
/* ====================================== Config for the Graph and Timeline ====================================== */
const GraphConfig: CosmographConfig = {
	backgroundColor: '#ffffff',
	pointGreyoutOpacity: 0.01,
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
	onClick(pointIndex) {
		if(pointIndex) handlePointClick(pointIndex)
	},
	onPointMouseOver(hoveredNodeId) {
		if(!isSelectionActive()){

		}
	},
	onPointsFiltered() {}


} 

const TimelineConfig: CosmographTimelineConfig = {
	accessor: 'date',
	allowPointerEvents: true,
	barRadius: 3,
	barPadding: 0.5
	

	// formatter(date) {
	// 	return new Date(date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
	// },

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

async function initializeGraph() {}

export function updateGraphConfig(config: CosmographInputConfig<Point, Link>) {
	graph.setConfig(config);
}

// export function updateTimelineConfig(config: CosmographTimelineInputConfig)

export function updateGraphData() {
	// const startTime = new Date().getTime();
	// console.log('Updating the graph');
	// Points.subscribe((PointsArray) => {
	//     graph.setData(PointsArray, get(links));
	// });
	// const endTime = new Date().getTime();
	// const duration = Math.round(endTime - startTime) / 1000;
	// console.log(`Time to set Data: ${duration} sec`);
}

export function updatePoints(newPoints: Point[]) {
	// make sure you update only unique
	// Points.update((existingPoints) => {
	//     const existingIds = new Set(existingPoints.map((Point) => Point.id));
	//     const uniqueNewPoints = newPoints.filter((newPoint) => !existingIds.has(newPoint.id));
	//     return [...existingPoints, ...uniqueNewPoints];
	// });
}

export function selectPointsInRange(arr: [[number, number], [number, number]]) {
	// // TODO: fix this function
	// graph.selectPointsInRange(arr);
	// selectedPoints.set(getSelectedPoints() as Point[]);
}

export function unselectPoints() {
	// selectedPoints.set([]);
	// graph.unselectPoints();
	// SelectedDateRange.set(undefined);
	// const search_bar_input = document.getElementById('search-bar-input') as HTMLInputElement;
	// search_bar_input.value = '';
	// SelectedSearchQuery.set('');
	// SelectedClusters.set([]);
}

/**
 * Gets all the selected Point objects.
 * @return An array of selected Point objects.
 * @todo very slow for 5M Points, need another way.
 */

export function getSelectedPoints() {
	// return get(selectedPoints);
	return graph.getSelectedPointIndices()
}

export function getSelectedPointsCount() {
	return graph.getSelectedPointIndices()?.length
}


export function isSelectedPoint(Point: Point): boolean {
	// const current = getSelectedPoints();
	// // Rebuild the set only if the selection changed
	// if (current !== lastSelected) {
	//     cachedIds = new Set(current.map((n) => n.id));
	//     lastSelected = current;
	// }
	// return cachedIds.has(Point.id);
}

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

export function updateSelectedPoints(thePoints: Point[]) {
	// selectedPoints.update((existingPoints) => {
	//     const existingIds = new Set(existingPoints.map((n) => n.id));
	//     const uniqueNewPoints = thePoints.filter((newPoint) => !existingIds.has(newPoint.id));
	//     return [...existingPoints, ...uniqueNewPoints];
	// });
	// graph.selectPoints(getSelectedPoints());
}

export function conditionalSelectPoints(thePoints: Point[]) {
	// get the matches
	// const newPoints = new Set(thePoints.map((n) => n.id));
	// const PointsToShowonGraph = getSelectedPoints().filter((n) => newPoints.has(n.id));
	// setSelectedPoints(PointsToShowonGraph);
}

export function fitViewofGraph() {
	// graph.fitView();
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



export function isSelectionActive(): boolean {
	if (getSelectedPointsCount() as number > 0) return true
	return false
}
export function getClusterPointsByClusterIds(cluster_ids: string[]): Point[] {
	// const ClusterPointIds = new Set(cluster_ids);
	// const filteredPoints = getRenderedPoints().filter(
	//     (Point) => ClusterPointIds.has(Point.id) && Point.isClusterPoint
	// );
	// return filteredPoints;
}
