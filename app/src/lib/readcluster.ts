import pkg from 'papaparse';
const { parse } = pkg;
import type { Node, Link, Cluster } from '$lib/types';
import { writable, get } from 'svelte/store';
import { formatDate } from './utils';
import { interpolateRgb } from "d3";

const nodes= writable<Node[]>([]);
let links=writable<Link[]>([])
const dataloaded = writable(false);
export let allClusters=writable<Cluster[]>([]);
export let ClustersTree:{[depth: number]: string[]};

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
    if (get(allClusters).length != 0) {
        const currentallClusters: Cluster[] = get(allClusters);
        // Use filter to get clusters that match the condition, and map to extract the id.
        const leafClusters: string[] = currentallClusters
            .filter(cluster => cluster.isLeaf && cluster.path.includes(cluster_id))
            .map(cluster => cluster.id);
        return leafClusters; 
    }

    // Optionally return an empty array if no clusters are found
    return [];
}

export async function getLabelsfromOpenSearch(){
	const response = await fetch(`api/opensearch/cluster`);
	const data = await response.json()
	
	if(Array.isArray(data)){
		const newClusters:Cluster[] = data.map(item => (
			{
				id : item._source.cluster_id,
				xCenter: item._source.x,
				yCenter: item._source.y,
				label: item._source.label,
				depth: item._source.depth,
				isLeaf: item._source.isLeaf,
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
				date: undefined,
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
	ClustersTree = createDepthClusterDict(get(allClusters));
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
			date: formatDate(item._source.date), // Assuming date will be set later
			color: getNodeColor(item._source.x,item._source.y,[[10.784323692321777,21.064863204956055],[12.669471740722656,15.152010917663574]],0.6),
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
	
async function load10k(from: number, size:number){
	await getNodesfromOpenSearch(from, size);
}

async function loadLables(){
	await getLabelsfromOpenSearch();
}

export { nodes, links, dataloaded, load10k, loadLables };

