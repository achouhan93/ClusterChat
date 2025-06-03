import { writable } from 'svelte/store';

// graph.ts
export let hierarchicalLabels = writable<boolean>(false);
export let document_specific = writable(true);
