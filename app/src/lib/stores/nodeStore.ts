import { writable, derived } from 'svelte/store';
import type { Node, Link, Cluster } from '$lib/types';

// graph.ts

export let selectedNodes = writable<Node[]>([]);
export let selectedNodesCount = writable<number>(0);

selectedNodes.subscribe((arr) => {
	selectedNodesCount.set(arr.length);
});

export let SelectedDateRange = writable<[Date, Date] | [number, number]>(undefined);
export let SelectedSearchQuery = writable<string>('');
export let SelectedClusters = writable<string[]>([]);
export const selectedClustersCount = writable<number>(0);

SelectedClusters.subscribe((arr) => {
	selectedClustersCount.set(arr.length);
});

export let selectMultipleClusters = writable<boolean>(false); // TODO: change to multiple Cluster selection
export let selectNodeRange: boolean = false;

export let hNode = writable<Node>();
export let hoveredNodeId = writable<string>('');
// export let hoveredNodeId = derived(hNode, ($hNode) => $hNode?.id ?? '');

// readcluster.ts
export const nodes = writable<Node[]>([]);
export let links = writable<Link[]>([]);
export const dataloaded = writable(false);
export let allClusters = writable<Cluster[]>([]);
export let allClusterNodes = writable<Node[]>([]);
export let ClustersTree = writable<{ [depth: number]: string[] }>([]);
