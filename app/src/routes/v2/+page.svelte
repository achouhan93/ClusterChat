<script lang="ts">
    import { onMount } from 'svelte';
	import { Cosmograph, type CosmographInputData} from 'cosmograph-v2';
	import { Schema, Table, tableFromArrays, tableFromIPC, tableFromJSON } from 'apache-arrow';
	import { toUint8Array } from 'apache-arrow/util/buffer';
	import type { Point } from '$lib/types';
	import type { CosmographPointInput } from 'cosmograph-v2/cosmograph/config';
    // import { readFileSync } from 'fs';

    let graph: Cosmograph

    function createGraph(points,config) {
        const container: HTMLElement = document.getElementById('main-graph');
        graph =  new Cosmograph(container, {points, ...config})
    }
    async function fetchFileFromUrl(url, fileName, mimeType) {
  try {
    // Fetch the file from the URL
    const response = await fetch(url);
    
    // Check if the request was successful
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // Get the data as a blob
    const blob = await response.blob();
    
    // Create a File object from the blob
    const file = new File([blob], fileName, { type: mimeType || blob.type });
    
    return file;
  } catch (error) {
    console.error('Error fetching the file:', error);
    return null;
  }
}
    onMount(async () => {
    try {
        // const arrowFile = await fetch("src/lib/data/cosmograph-points.arrow")
        // const points = await tableFromIPC(arrowFile)
        // console.table([...points]);
        // const config = await fetch("src/lib/data/cosmograph-config.json")
        // console.log(points)
        // console.log(config)
        // createGraph(points,config)


        const points = await fetch('/data/cosmograph-points-200K.arrow').then(res => res.blob())
        const config = await fetch('/data/cosmograph-config.json').then(res => res.json())
        console.log(config)
        const pointsFile = new File([points], 'cosmograph-points.arrow', { type: 'application/octet-stream' })
        const container: HTMLDivElement = document.getElementById('main-graph');
        const cosmograph = new Cosmograph(container, { points: pointsFile, ...config })
        const endTimeInMs = new Date().getTime();
        const durationInMs = endTimeInMs - startTimeInMs;


        
        
    } catch (err) {
        console.error('Error loading arrow file:', err);
    }
    
    
});


</script>

		<div id="main-graph">
		</div>

<style>
    	#main-graph{
		height: 100%;
		width: 100%;
		position: absolute;
		scroll-behavior: smooth;
		background-color: #fff;
	}
</style>




   

