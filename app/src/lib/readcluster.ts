import pkg from 'papaparse';
const { parse } = pkg;
import type { Node, Link } from '$lib/types';
import { writable } from 'svelte/store';
import { formatDate } from './utils';

const nodes= writable<Node[]>([
	/* {id: "38898713", x: -1.2475016280453854, y: -0.7180506886729104,cluster: 17, date: formatDate("12/12/2024")} */
]);
let links: Link[] = [];
const dataloaded = writable(false);

export async function getNodesfromOpenSearch(from:number, size: number) {
const response = await fetch(`/api/opensearch/${from}/${size}`);
const data = await response.json();
// TODO
if (Array.isArray(data)) {

	const newNodes:Node[] = data.map(item => (
		{
			id: item._source.documentID,
			x: item._source.x,
			y: item._source.y,
			cluster: item._source.cluster_label,
			date: new Date()  // Assuming date will be set later
		} satisfies Node
));

nodes.update(existingNodes => {
	// Append new nodes to the existing ones
	return [...existingNodes, ...newNodes];
  });
} else {
	console.error("Expected an array but got:", data);
}
}
	
async function load10k(from: number, size:number){
	await getNodesfromOpenSearch(from, size);
}

export { nodes, links, dataloaded, load10k };

/* Load nodes from the CSV file containing the nodes data after cluster analysis
async function loadNodes() {
	try {
		const response = await fetch('/src/data/nodes.csv');
		const file_nodes = await response.text();
		const result_nodes = parse(file_nodes, { header: false });
		const nodesData: any[] = result_nodes.data;
		// TODO: 5000 only for testing, nodesData.length for production
		const nodesDataLength: number = nodesData.length;
		for (let index = 1; index < nodesDataLength; index += 1) {
			if (nodesData[index][1] !== '-1') {
				const newNode: Node = {
					id: nodesData[index][0],
					cluster: parseInt(nodesData[index][1]),
					x: parseFloat(nodesData[index][2]),
					y: parseFloat(nodesData[index][3]),
					color: nodesData[index][4],
					size: 0.15,
					title: nodesData[index][5],
					date: formatDate(nodesData[index][6]) || undefined
				};
				nodes.push(newNode);

				const newLink: Link = {
					source: nodesData[index][0],
					target: nodesData[index][0],
					date: formatDate(nodesData[index][6]) || undefined
				};
				links.push(newLink);
			}
		}
	} catch (error) {
		// Handle errors (e.g., fetch failed, parsing issues)
		console.error('Error loading nodes:', error);
	}
}


async function loadData() {
	await loadNodes();
}



// connecting with openSearch

// load 5000 Nodes */
