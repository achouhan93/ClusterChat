<script lang="ts">
	import { selectedNodes, DateRange } from "$lib/graph";
    import { ChevronRight, ChevronLeft } from "lucide-svelte";
    import { get, readable,writable } from 'svelte/store';
    import type { Node, Cluster } from "$lib/types";
	import { allClusters } from "$lib/readcluster";


    let toShow= writable<Node[]>([])
    let abstract = writable<string>("");
    let currentPage = writable<number>(1)
    let pageCount = writable<number>(0)
  

    const handleLeftClick = () => {
        if ($currentPage != 1) currentPage.update((value) => value -1)
    }

    const handleRightClick = () => {
        if($currentPage != $pageCount) currentPage.update((value) => value +1)
    }

   async function fetchAbstractById(id:string):Promise<string>{
        const response = await fetch(`/api/opensearch/findabstract/${id}`)
        const data = await response.json()
        return data[0]._source.abstract
    }
    async function updateAbstract(nodeId: string) {
        const abstractText = await fetchAbstractById(nodeId); // Wait for the result
        abstract.set(abstractText); // Set the resolved value in the store
    }

    function formatDateRange(date:[Date,Date]){
        return `${date[0].toLocaleString('en-US', { month: 'short' })} ${date[0].getDate()} -  
        ${date[1].toLocaleString('en-US', { month: 'short' })} ${date[1].getDate()}, ${date[1].getFullYear()}`
    }
    
    function getClusterInformationFromNode(node:Node):string[]{
        const cluster_id:string = node.cluster as unknown as string
        const clusterinfo:Cluster = get(allClusters).find(cluster =>  cluster.id === cluster_id)
        const clusterLinage: string[] = clusterinfo.path.split("/")
        const foundClusters = get(allClusters).filter(cluster => clusterLinage.includes(cluster.id))
        foundClusters.sort(cluster => cluster.depth)
        const foundClusterName: string[] = foundClusters.map(c => c.label)
        return foundClusterName
    }

    selectedNodes.subscribe(newnodes =>{
        toShow.set(newnodes)
        if($selectedNodes.length == 0){
            pageCount.set(0)
        } else {
            pageCount.set(newnodes.length)
        }

    })

  

    $: if ($toShow.length !=0) {updateAbstract(get(toShow)[$currentPage -1]?.id) }


    // TODO: make pagation actually work
    // TODO: update the nodes in the background after showing 

</script>

<div class="node-information-view">
    <h4>Node Information</h4>
    <div class="node-info-list">

        {#if $toShow.length !=0}
        
    

            {#if $toShow.length > 1}
            <div class="pagation-btns">
                <button class="pagation-btn" on:click={handleLeftClick}><ChevronLeft/></button>
                <button class="pagation-btn" on:click={handleRightClick}><ChevronRight/></button>
                {$currentPage} of {$pageCount}
            </div>
            {/if}
            {#if $DateRange != undefined}
            <div class="selected-date-range">
                Selected Date Range: <span> {formatDateRange($DateRange)}</span>
            </div>
    
            {/if}

        <div class="info-field">
            <span class="info-field-title">title</span>
            <div class="info-field-content">{$toShow[$currentPage -1].title}</div>            
        </div>

        <div class="info-field">
            <span class="info-field-title">abstract</span>
            <div class="info-field-content abstract">{$abstract}</div>            
        </div>
        <div class="info-field">
            <span class="info-field-title">cluster</span>
            <div class="info-field-content abstract">
                {getClusterInformationFromNode($toShow[$currentPage -1])}
                <!-- <ul>
                {#each getClusterInformationFromNode($toShow[$currentPage -1]) as clustername}
                <li>{clustername}</li>
                {/each}
            </ul>  -->
            </div>        
   
        </div>
        {/if}
    </div>
</div>


<style>
	h4 {
		color: black;
		text-align: center;
		align-self: center;
		padding: var(--size-2);
	}
    .node-information-view {
        display: flex;
        flex-direction: column;
    }
    .info-field {
        margin: var(--size-4);
    }
    .info-field-title {
        color: var(--blue-8);
        font-weight: var(--font-weight-8);
        padding: var(--size-2);
        size: var(--font-size-1);
    }
    .info-field-content{
        height: fit-content;
        font-size: small;
        padding: var(--size-2);
        color: var(--text-1-light);
        background-color: var(--surface-4-light);
        border-radius: var(--radius-2);
    }
    .info-field-content.abstract {
        overflow-y: auto; /* Allows vertical scrolling */
		overflow-x: hidden;
        height:  var(--size-fluid-5);
		display: flex;
    }
    .pagation-btns {
        margin-bottom: var(--size-2);
        margin-left: var(--size-1);
        gap: var(--size-1);
        display: flex;
        font-size: small;
    }
    .pagation-btn {
        background-color: var(--blue-8);
        height: fit-content;
        max-height: var(--size-px-1);
        box-shadow: none;
    }
    .pagation-btn:hover{
        box-shadow: none;
    }
    .selected-date-range {
        width: fit-content;
        padding: var(--size-2);
        border-radius: var(--radius-5);
        background-color: var(--blue-4);
        margin-bottom: var(--size-2);
        font-size: small;
    }

</style>