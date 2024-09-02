import pkg from 'papaparse';
const { parse } = pkg;
import type { Node, Link } from '$lib/types';
import { writable } from 'svelte/store';
import { formatDate } from './utils';

let nodes: Node[] = [];
let links: Link[] = [];
const dataloaded = writable(false);

// Load nodes from the CSV file containing the nodes data after cluster analysis
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

export { loadData, nodes, links, dataloaded };

// connecting with openSearch

// load 5000 Nodes

export async function getNodesfromOpenSearch(size: number) {
	const response = await fetch(`/api/opensearch/${size}`);
	const data = await response.json();

	// TODO
	/*	if (Array.isArray(data)) {
		data.forEach((item, index) => {
			const newNode: Node = {
				id: item._source.id
				// ...
			}
			nodes.push(newNode);
		});
	} else {
		console.error("Expected an array but got:", data);
	}
*/
}
