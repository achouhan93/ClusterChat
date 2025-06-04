import { writable } from 'svelte/store';

// graph.ts
export let hierarchicalLabels = writable<boolean>(false);
export let document_specific = writable(true);

// InfoView.ts
export let pageCount = writable<number>(0);
