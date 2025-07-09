import pkg from 'papaparse';
const { parse } = pkg;
import type { Node, Link, Cluster } from '$lib/types';
import { writable, get } from 'svelte/store';
import { formatDate } from './utils';
import { interpolateRgb } from 'd3';
import { tableFromIPC, type Table, type Vector, RecordBatchReader, RecordBatch } from 'apache-arrow';

import {
	nodes,
	links,
	dataloaded,
	allClusters,
	allClusterNodes,
	ClustersTree
} from '$lib/stores/nodeStore';

export let ColorPalette: Record<string, string>;

export function getNodeColor(
	x: number,
	y: number,
	fitView: [[number, number], [number, number]],
	opacity: number
): string {
	// Destructure fitView coordinates
	const [[xMin, yMax], [xMax, yMin]] = fitView;

	// Normalize x and y based on fitView bounds to be between 0 and 1
	const xNormalized = (x - xMin) / (xMax - xMin);
	const yNormalized = (y - yMin) / (yMax - yMin);

	// Interpolate colors based on the normalized x and y
	const colorX = interpolateRgb('red', 'blue')(xNormalized); // X-axis gradient from red to blue
	const colorY = interpolateRgb('yellow', 'green')(yNormalized); // Y-axis gradient from yellow to green

	// Combine the two interpolated colors (this can be adjusted based on your needs)
	const mixedColor = interpolateRgb(colorX, colorY)(0.4); // Combine them at 50% mix, feel free to adjust
	const rgbValues = mixedColor.match(/\d+/g)!.map(Number); // Extract RGB values as an array of numbers
	return `rgba(${rgbValues[0]}, ${rgbValues[1]}, ${rgbValues[2]}, ${opacity})`;
}
function generateClusterColors(clusterIds: string[]): Record<string, string> {
	const colors: Record<string, string> = {};
	const totalClusters = clusterIds.length;

	clusterIds.forEach((clusterId, index) => {
		// Vary hue with a larger step for better contrast
		const hue = (index * 137.5) % 360; // 137.5 ensures good distribution of colors

		// Alternate saturation and lightness for additional contrast
		const saturation = index % 2 === 0 ? 70 : 50; // Alternates between 70% and 50%
		const lightness = index % 2 === 0 ? 45 : 55; // Alternates between 45% and 55%

		colors[clusterId] = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
	});

	return colors;
}

function createDepthClusterDict(clusters: Cluster[]): { [key: number]: string[] } {
	const depthClusterDict: { [key: number]: string[] } = {};

	clusters.forEach((cluster) => {
		const { depth, id } = cluster;

		// If the depth is key in the dictionary, append to the array
		if (depthClusterDict[depth]) {
			depthClusterDict[depth].push(id);
		} else {
			// else, create a new array for that depth
			depthClusterDict[depth] = [id];
		}
	});

	return depthClusterDict;
}

export function getAssociatedLeafs(cluster_id: string, cluster_label: string): string[] {
	const currentallClusters: Cluster[] = get(allClusters);
	if (currentallClusters.length != 0) {
		// Use filter to get clusters that match the condition, and map to extract the id.
		let leafClusters: string[] = currentallClusters
			.filter(
				(cluster) =>
					(cluster.isLeaf && cluster.path.split('/').includes(cluster_id)) ||
					(cluster.isLeaf && cluster.label === cluster_label)
			)
			.map((cluster) => cluster.id);
		// console.dir(leafClusters)
		return leafClusters;
	}

	// Optionally return an empty array if no clusters are found
	return [];
}



function hashString(str: string): number {
	let hash = 0;
	for (let i = 0; i < str.length; i++) {
		hash = (hash << 5) - hash + str.charCodeAt(i);
		hash |= 0; // Convert to 32bit integer
	}
	return Math.abs(hash);
}

function hslToRgba(h: number, s: number, l: number): [number, number, number, number] {
	s /= 100;
	l /= 100;

	const c = (1 - Math.abs(2 * l - 1)) * s;
	const x = c * (1 - Math.abs((h / 60) % 2 - 1));
	const m = l - c / 2;

	let r = 0, g = 0, b = 0;

	if (h < 60) {
		r = c; g = x; b = 0;
	} else if (h < 120) {
		r = x; g = c; b = 0;
	} else if (h < 180) {
		r = 0; g = c; b = x;
	} else if (h < 240) {
		r = 0; g = x; b = c;
	} else if (h < 300) {
		r = x; g = 0; b = c;
	} else {
		r = c; g = 0; b = x;
	}

	return [
		Math.round((r + m) * 255),
		Math.round((g + m) * 255),
		Math.round((b + m) * 255),
		1 // full alpha
	];
}

export function getColorForCluster(clusterId: string): string{
	const hash = hashString(clusterId);
	const hue = hash % 360;
	const saturation = (hash % 2 === 0) ? 70 : 50;
	const lightness = (hash % 3 === 0) ? 45 : 55;

	return hslToRgba(hue, saturation, lightness).toString();
}

export async function getLabelsfromOpenSearch() {
	const response = await fetch(`/api/opensearch/clusters`);
	const data = await response.json();

	if (Array.isArray(data)) {
		const newClusters: Cluster[] = data.map((item) => ({
			id: item._source.cluster_id,
			xCenter: item._source.x,
			yCenter: item._source.y,
			label: item._source.label,
			depth: item._source.depth,
			isLeaf: item._source.is_leaf,
			path: item._source.path
		}));
		const clusterLabelNodes: Node[] = data.map((item) => ({
			id: item._source.cluster_id,
			title: item._source.label,
			x: item._source.x,
			y: item._source.y,
			isClusterNode: true,
			cluster: item._source.path,
			date: item._source.depth,
			color: '#fff'
		}));
		allClusters.update((existingClusters) => {
			return [...existingClusters, ...newClusters];
		});
		nodes.update((existingNodes) => {
			// Append new nodes to the existing ones
			return [...existingNodes, ...clusterLabelNodes];
		});

		allClusterNodes.set(clusterLabelNodes);
	}
	// TODO: save tree of depth and clusters
	if (get(allClusters).length != 0) ClustersTree.set(createDepthClusterDict(get(allClusters)));
	ColorPalette = generateClusterColors(get(allClusters).map((c) => c.id));
}

async function extractClustersFromTable(table:Table){
	const newClusters:Cluster[] = []
	const clusterLabelNodes:Node[] = []

	for (const batch of table.batches) {
		const numRows = batch.numRows;

		const idVec = batch.getChild("id");
		const xVec = batch.getChild("x");
		const yVec = batch.getChild("y");
		const labelVec = batch.getChild("label");
		const depthVec = batch.getChild("depth");
		const isLeafVec = batch.getChild("is_leaf");
		const pathVec = batch.getChild("path");

		// Preallocate output arrays (optional, useful if you know total count)
		const clusters: Cluster[] = new Array(numRows);
		const labelNodes: Node[] = new Array(numRows);

		for (let i = 0; i < numRows; i++) {
			const id = idVec?.get(i);
			const x = xVec?.get(i);
			const y = yVec?.get(i);
			const label = labelVec?.get(i);
			const depth = depthVec?.get(i);
			const isLeaf = isLeafVec?.get(i);
			const path = pathVec?.get(i);

			clusters[i] = {
			id,
			xCenter: x,
			yCenter: y,
			label,
			depth,
			isLeaf,
			path
			};

			labelNodes[i] = {
			id,
			title: label,
			x,
			y,
			isClusterNode: true,
			cluster: path,
			date: depth,
			color: '#fff'
			};
		}

		// Append all at once (faster than push per iteration)
		newClusters.push(...clusters);
		clusterLabelNodes.push(...labelNodes);	
	}

		return {newClusters,clusterLabelNodes}
}

async function fetchLabelsfromArrow(filename:string){
	const response = await fetch(filename);
	const table: Table = await tableFromIPC(await response.arrayBuffer());
	// console.log("Table Schema",table.schema)
	if(table) {

		const {newClusters, clusterLabelNodes} = await extractClustersFromTable(table)
		// console.log(newClusters[0])
		allClusters.update((existingClusters) => {
			return [...existingClusters, ...newClusters];
		});
		nodes.update((existingNodes) => {
			return [...existingNodes, ...clusterLabelNodes];
		});

		allClusterNodes.set(clusterLabelNodes);
	

		if (get(allClusters).length != 0) ClustersTree.set(createDepthClusterDict(get(allClusters)));
		ColorPalette = generateClusterColors(get(allClusters).map((c) => c.id));
	} else {
		console.error('Expected an array but got:', response);
	}

}

/* function getClusterDepth(cluster_id:string){
	const foundMatch= allClusters.find(cluster =>
		cluster.id as string === cluster_id || `cluster_${cluster_id}` === cluster_id 
	)
	return foundMatch?.depth || foundMatch
} */


// Use it in your main function
async function extractPointsFromTable(table:Table){
	const numRows = table.numRows;
	const startTime = Date.now();
	const idVec = table.getChild("id");
	const titleVec = null//table.getChild("title");
	const xVec = table.getChild("x");
	const yVec = table.getChild("y");
	const clusterIdVec = table.getChild("cluster_id");
	const dateVec = table.getChild("date");

	const newNodes: Node[] = new Array(numRows);
	const newLinks: Link[] = new Array(numRows);

	for (let i = 0; i < numRows; i++) {
		const clusterId = clusterIdVec?.get(i);
		const date = dateVec?.get(i);

		newNodes[i] = {
			id: idVec?.get(i),
			title: '',//titleVec?.get(i),
			x: xVec?.get(i),
			y: yVec?.get(i),
			isClusterNode: false,
			cluster: clusterId,
			date,
			color: ColorPalette[clusterId] || '#000'
		};

		newLinks[i] = {
			source: '',
			target: '',
			date: formatDate(date)
		};
	}


		const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
		console.log(`\rFetched: ${numRows} Rows | Time: ${elapsedSeconds}s`);
	
	return { newNodes, newLinks };

}
async function extractPointsFromTableTODO(table:Table){
	const newNodes: Node[] = [];
	const newLinks: Link[] = [];

	const startTime = Date.now();

	for (const batch of table.batches) {
		const numRows = batch.numRows;

		// Cache vectors outside loop
		const idVec = batch.getChild("id");
		const titleVec = batch.getChild("title");
		const xVec = batch.getChild("x");
		const yVec = batch.getChild("y");
		const clusterIdVec = batch.getChild("cluster_id");
		const dateVec = batch.getChild("date");

		// Optional: Preallocate for slight perf boost on large batches
		const nodes: Node[] = new Array(numRows);
		const links: Link[] = new Array(numRows);

		for (let i = 0; i < numRows; i++) {
			const clusterId = clusterIdVec?.get(i);
			const date = dateVec?.get(i);
			
			const node: Node = {
			id: idVec?.get(i),
			title: titleVec?.get(i),
			x: xVec?.get(i),
			y: yVec?.get(i),
			isClusterNode: false,
			cluster: clusterId,
			date: date,
			color: ColorPalette[clusterId] || '#000'  // safe fallback
			};

			const link: Link = {
			source: '',      // Fill later if needed
			target: '',      // Fill later if needed
			date: formatDate(date)
			};

			nodes[i] = node;
			links[i] = link;
		}

		newNodes.push(...nodes);
		newLinks.push(...links);

		const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
		console.log(`\rFetched: ${numRows} Rows | Time: ${elapsedSeconds}s`);
	}

	return { newNodes, newLinks };
}
async function fetchPointsfromArrow(filename: string) {
	const response = await fetch(filename);
	const table: Table = await tableFromIPC(await response.arrayBuffer());
	if (table){
		const {newNodes, newLinks} = await extractPointsFromTable(table)
		nodes.update((existingNodes) => {
			// Append new nodes to the existing ones
			return [...existingNodes, ...newNodes];
		});
		links.update((existingLinks) => {
			return [...existingLinks, ...newLinks];
		});
	} else {
		console.error('Expected an array but got:', response);
	}
}


export async function getNodesfromOpenSearch(from: number, size: number) {
	const response = await fetch(`/api/opensearch/nodes/${from}/${size}`);
	const data = await response.json();
	// TODO
	if (Array.isArray(data)) {
		const newNodes: Node[] = data.map(
			(item) =>
				({
					id: item._source.document_id,
					title: item._source.title,
					x: item._source.x,
					y: item._source.y,
					isClusterNode: false,
					cluster: item._source.cluster_id,
					date: item._source.date, //formatDate(item._source.date), // Assuming date will be set later
					color: ColorPalette[item._source.cluster_id]
				}) satisfies Node
		);
		const newLinks: Link[] = data.map(
			(item) =>
				({
					source: '',
					target: '',
					date: formatDate(item._source.date)
				}) satisfies Link
		);

		nodes.update((existingNodes) => {
			// Append new nodes to the existing ones
			return [...existingNodes, ...newNodes];
		});
		links.update((existingLinks) => {
			return [...existingLinks, ...newLinks];
		});
	} else {
		console.error('Expected an array but got:', data);
	}
}
async function fetchDocumentIds(cluster_ids: string[]) {
	const response = await fetch('/api/opensearch/clusterids', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},

		body: JSON.stringify({ cluster_ids }) // Send the array in the request body as JSON
	});

	const data = await response.json();
	const newNodes: Node[] = data.map(
		(item: any) =>
			({
				id: item._source.document_id,
				title: item._source.title,
				x: item._source.x,
				y: item._source.y,
				isClusterNode: false,
				cluster: item._source.cluster_id,
				date: item._source.date, //formatDate(item._source.date), // Assuming date will be set later
				color: ColorPalette[item._source.cluster_id]
			}) satisfies Node
	);

	// update the view
	nodes.update((existingNodes) => {
		const existingIds = new Set(existingNodes.map((node) => node.id));

		const uniqueNewNodes = newNodes.filter((newNode) => !existingIds.has(newNode.id));

		return [...existingNodes, ...uniqueNewNodes];
	});
	// updateGraphData()
}

async function LoadNodesByCluster(cluster_ids: string[]) {
	await fetchDocumentIds(cluster_ids);
}

async function loadNodes() {

	const filename="/data/nodes.arrow"
	await fetchPointsfromArrow(filename)
}

async function loadLabels() {

	const filename="/data/clusters.arrow"
	await fetchLabelsfromArrow(filename)
}

export { loadNodes, loadLabels, LoadNodesByCluster };
