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

import { tableFromIPC, RecordBatchReader, RecordBatch } from 'apache-arrow';
// Other
import '../../app.css';
import type { Node, Link, Cluster, Point } from '$lib/types';
;
import { get, derived, writable } from 'svelte/store';
import { LabelsKeys, type CosmographPointInput } from 'cosmograph-v2/cosmograph/config';
import { page } from '$app/state';

// Useful global variables
export let graph: Cosmograph;
let arrowReader: AsyncIterableIterator<any> | null = null
let timeline: CosmographTimeline

let batchCounter = writable<number>(2)
let intervalId: NodeJS.Timeout | null = null

/* ====================================== Graph and Timeline Event Handlers ====================================== */
isSelectionActive.subscribe((active) => {
    console.log(`isSelectionActive?: ${active}`)
	if(!active) numberOfSelectedPoints.set(0)
})

const handlePointClick = async (index:number) => {
    if (index && !get(isSelectionActive) && get(document_specific)) {
        setSelectPoint(index)
    }
};
const handlePointsFiltered = async (table: CosmographData) => {
		numberOfSelectedPoints.set(table.numRows)
        isSelectionActive.set(true)
}
const handleZoomEnd = async () => {
	console.log("Entered handleZoomEnd")
	// const points = await tableFromIPC(await fetch(`/data/cosmograph-points-batch-${batchCounter}.arrow`))
	
	 await updateGraphData(await loadNextBatch())

	// batchCounter++;
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
    pointSize: 2, 
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
    // onClick(pointIndex) {
    //     if(pointIndex){ 
    //         handlePointClick(pointIndex) 
    //         outputLog(pointIndex)
    //     } else {
    //         unselectAllPoints()
    //     }  
    // },
    onPointMouseOver(hoveredPointIndex) {
        if(!get(isSelectionActive)){

        }
    },
    // very useful for date selection
    onPointsFiltered(SelectedPointsTable) {
		console.log(`onPointsFiltered: ${SelectedPointsTable.numRows}`)
        handlePointsFiltered(SelectedPointsTable)	
    },


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
	// const points = await fetch(pointsPath).then(res => res.blob())
	// const pointsFile = new File([points], 'cosmograph-points.arrow', { type: 'application/octet-stream' })
	const pointsConfig = await fetch(pointsConfigPath).then(res => res.json())
	const pointsFile = await tableFromIPC(await fetch(pointsPath))
	const container: HTMLElement = document.getElementById('main-graph');
	const ConfigData: CosmographConfig = { 
		points: pointsFile,
		...pointsConfig,
		...GraphConfig
	}
	graph = new Cosmograph(container, ConfigData)
	console.log(pointsFile.schema)
}


export async function initArrowReaderOnce(url: string) {
  if (arrowReader) return

  const response = await fetch(url)
  const reader = await RecordBatchReader.from(response.body!)
  arrowReader = reader[Symbol.asyncIterator]() // get batch-by-batch access
}

export async function loadNextBatch() {
  if (!arrowReader) return []

  const { value: batch, done } = await arrowReader.next()
  if (done || !batch) return []
  return batch
}
export async function loadBatchEverySecond(){
	const points = await loadNextBatch()
	if(!points) clearInterval(intervalId)
	updateGraphData(points)
}

export async function startStreaming(url: string) {
  console.log('Starting streaming from', url)
  await initArrowReaderOnce(url)
  console.log('Reader initialized')
  intervalId = setInterval(() => {
    console.log('Interval triggered')
    loadBatchEverySecond()
  }, 5000)
}



function stopStreaming() {
  if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
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


export async function updateGraphData(pointData:CosmographPointInput[]) {
	graph.addPoints(pointData)

}

// export async function updateGraphDataInterval() {
// 	const pointsPath = `/data/cosmograph-points-batch-${get(batchCounter)}.arrow`
// 	const points = await fetch(pointsPath)
// 	if(get(batchCounter) === 5) clearInterval(intervalId)
// 	const pointsFile = await tableFromIPC(points)
// 	intervalId = setInterval(() => {
//     console.log('Interval triggered')
// 	console.log(`Batch Counter: ${get(batchCounter)}`)
//     updateGraphData(pointsFile)
//   }, 30000)
//   batchCounter.update((value) => value+1 )

// }



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
	selectedPointsIds.set(pointIds as unknown as number[])
}


export function unselectAllPoints() {
	graph.unselectAllPoints()
	console.log("unselectAllPoints")
	isSelectionActive.set(false)
	selectedPointsIds.set([])
}

export function unselectPoint() {
	graph.unselectPoint()
	if(get(numberOfSelectedPoints) === 0) { //getSelectedPointCount() === 0
		console.log("unselectPoint")
		isSelectionActive.set(false)
	}
}

export async function getPointIndicesByIds(ids:number[]){
	return await graph.getPointIndicesByIds(ids as unknown as string[])
}

export function fitViewofGraph() {
	graph.fitView();
}

async function streamArrow(url: string) {
  const response = await fetch(url);

  if (!response.body) {
    throw new Error("Streaming not supported by this browser.");
  }

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value!);
  }

  const fullBuffer = concatChunks(chunks);
  const table = tableFromIPC(fullBuffer); // or use `tableFromIPC(chunks)` for some versions
  return table;
}

function concatChunks(chunks: Uint8Array[]): Uint8Array {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Uint8Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
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

export function getClusterPointsByClusterIds(cluster_ids: string[]): Point[] {
	// const ClusterPointIds = new Set(cluster_ids);
	// const filteredPoints = getRenderedPoints().filter(
	//     (Point) => ClusterPointIds.has(Point.id) && Point.isClusterPoint
	// );
	// return filteredPoints;
}
// async function fetchCosmographPoints(url: string): Promise<CosmographPointInput[]> {
//   const response = await fetch(url);
//   const table = await tableFromIPC(response);

//   const rows: CosmographPointInput[] = [];

//   for (const row of table) {
//     const point: Record<string, any> = {};

//     for (const key in row) {
//       if (key === 'date') {
//         // 🧠 Force strict integer (not float!) and no Date object
//         point.date = Number.isFinite(row.date) ? Math.trunc(row.date as number) : 0;
//       } else {
//         point[key] = row[key];
//       }
//     }

//     rows.push(point as CosmographPointInput);
//   }

//   return rows;
// }
// async function fetchArrowBatches(url: string) {
//   const response = await fetch(url);
//   const reader = await RecordBatchReader.from(response.body!);

//   const points: any[] = [];

//   for await (const batch of reader) {
// 	const idCol = batch.getChild("id");
//     const xCol = batch.getChild("x");
//     const yCol = batch.getChild("y");
//     const labelCol = batch.getChild("title"); // optional
//     const dateCol = batch.getChild("date");   // 🚨 this retains timestamp[s] type

//     for (let i = 0; i < batch.numRows; i++) {
//       points.push({
// 		id: idCol?.get(i),
//         x: xCol?.get(i),
//         y: yCol?.get(i),
//         title: labelCol?.get(i),
//         date: dateCol?.get(i), // ✅ remains timestamp[s], not JS double
//       });
//     }
//   }

//   return points;
// }
