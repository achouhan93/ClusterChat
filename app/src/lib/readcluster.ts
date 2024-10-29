import pkg from 'papaparse';
const { parse } = pkg;
import type { Node, Link, Cluster } from '$lib/types';
import { writable, get } from 'svelte/store';
import { formatDate } from './utils';
import { interpolateRgb } from "d3";
import {updateGraphData } from './graph';

const nodes= writable<Node[]>([]);
let links=writable<Link[]>([])
const dataloaded = writable(false);
export let allClusters=writable<Cluster[]>([]);
export let ClustersTree=writable<{[depth: number]: string[]}>([])
export let ColorPalette:Record<string,string>

export function getNodeColor(x: number, y: number, fitView: [[number, number], [number, number]], opacity:number): string {
    // Destructure fitView coordinates
    const [[xMin, yMax], [xMax, yMin]] = fitView;

    // Normalize x and y based on fitView bounds to be between 0 and 1
    const xNormalized = (x - xMin) / (xMax - xMin);
    const yNormalized = (y - yMin) / (yMax - yMin);

    // Interpolate colors based on the normalized x and y
    const colorX = interpolateRgb("red", "blue")(xNormalized);  // X-axis gradient from red to blue
    const colorY = interpolateRgb("yellow", "green")(yNormalized);  // Y-axis gradient from yellow to green

    // Combine the two interpolated colors (this can be adjusted based on your needs)
    const mixedColor = interpolateRgb(colorX, colorY)(0.4);  // Combine them at 50% mix, feel free to adjust
	const rgbValues = mixedColor.match(/\d+/g)!.map(Number); // Extract RGB values as an array of numbers
    return  `rgba(${rgbValues[0]}, ${rgbValues[1]}, ${rgbValues[2]}, ${opacity})`;
}
function generateClusterColors(clusterIds: string[]): Record<string, string> {
    const colors: Record<string, string> = {};
    const totalClusters = clusterIds.length;

    clusterIds.forEach((clusterId, index) => {
        // Vary hue with a larger step for better contrast
        const hue = (index * 137.5) % 360; // 137.5 ensures good distribution of colors

        // Alternate saturation and lightness for additional contrast
        const saturation = (index % 2 === 0) ? 70 : 50; // Alternates between 70% and 50%
        const lightness = (index % 2 === 0) ? 45 : 55; // Alternates between 45% and 55%

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

  export function getAssociatedLeafs(cluster_id: string): string[] {
    const currentallClusters: Cluster[] = get(allClusters);
			if (currentallClusters.length != 0) {
				// Use filter to get clusters that match the condition, and map to extract the id.
				let leafClusters: string[] = currentallClusters
					.filter(cluster => cluster.isLeaf && cluster.path.includes(cluster_id))
					.map(cluster => cluster.id);
					// console.dir(leafClusters)
				return leafClusters; 
			}
		
			// Optionally return an empty array if no clusters are found
			return [];
		}
		

export async function getLabelsfromOpenSearch(){
	const response = await fetch(`/api/opensearch/cluster`);
	const data = await response.json()
	
	if(Array.isArray(data)){
		const newClusters:Cluster[] = data.map(item => (
			{
				id : item._source.cluster_id,
				xCenter: item._source.x,
				yCenter: item._source.y,
				label: item._source.label,
				depth: item._source.depth,
				isLeaf: item._source.is_leaf,
				path: item._source.path
			}
		));
		const clusterLabelNodes:Node[] = data.map(item => (
			{
				id: item._source.cluster_id,
				title:item._source.label,
				x: item._source.x,
				y: item._source.y,
				isClusterNode: true,
				cluster : item._source.path,
				date: item._source.depth,
				color: "#fff",
			}
		));
		allClusters.update(existingClusters => { return [...existingClusters, ...newClusters]})
		nodes.update(existingNodes => {
			// Append new nodes to the existing ones
			return [...existingNodes, ...clusterLabelNodes];
		  });
		  
		 
		
	}
	// TODO: save tree of depth and clusters
	if(get(allClusters).length != 0)
	ClustersTree.set(createDepthClusterDict(get(allClusters)));
	ColorPalette = generateClusterColors(get(allClusters).map(c => c.id))
}

/* function getClusterDepth(cluster_id:string){
	const foundMatch= allClusters.find(cluster =>
		cluster.id as string === cluster_id || `cluster_${cluster_id}` === cluster_id 
	)
	return foundMatch?.depth || foundMatch
} */

export async function getNodesfromOpenSearch(from:number, size: number) {
const response = await fetch(`/api/opensearch/nodes/${from}/${size}`);
const data = await response.json();
// TODO
if (Array.isArray(data)) {

	const newNodes:Node[] = data.map(item => (
		{
			id: item._source.document_id,
			title:item._source.title,
			x: item._source.x,
			y: item._source.y,
			isClusterNode: false,
			cluster: item._source.cluster_id,
			date: item._source.date,//formatDate(item._source.date), // Assuming date will be set later
			color: ColorPalette[item._source.cluster_id]
		} satisfies Node
));
	const newLinks:Link[] = data.map(item => (
		{
			source: "",
			target:"",
			date: formatDate(item._source.date)
		} satisfies Link
	));

	nodes.update(existingNodes => {
	// Append new nodes to the existing ones
	return [...existingNodes, ...newNodes];
  });
  	links.update(existingLinks => {
		return [...existingLinks, ...newLinks]
	})
} else {
	console.error("Expected an array but got:", data);
}
}
async function fetchDocumentIds(cluster_ids:string[]){
	const response = await fetch('/api/opensearch/clusterids', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },

        body: JSON.stringify({ cluster_ids }) // Send the array in the request body as JSON
    });

    const data = await response.json();
	const newNodes:Node[] = data.map(item => (
		{
			id: item._source.document_id,
			title:item._source.title,
			x: item._source.x,
			y: item._source.y,
			isClusterNode: false,
			cluster: item._source.cluster_id,
			date: item._source.date,//formatDate(item._source.date), // Assuming date will be set later
			color: ColorPalette[item._source.cluster_id],
		} satisfies Node
	));
	


	// update the view
	nodes.update(existingNodes => {
		const existingIds = new Set(existingNodes.map(node => node.id));
	
		const uniqueNewNodes = newNodes.filter(newNode => !existingIds.has(newNode.id));
	
		return [...existingNodes, ...uniqueNewNodes];
	});
		// updateGraphData()


}

async function LoadNodesByCluster(cluster_ids:string[]){
	await fetchDocumentIds(cluster_ids)
}

	
async function load10k(from: number, size:number){
	await getNodesfromOpenSearch(from, size);
}

async function loadLables(){
	await getLabelsfromOpenSearch();
}

export { nodes, links, dataloaded, load10k, loadLables,LoadNodesByCluster };

