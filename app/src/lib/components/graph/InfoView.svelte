<script lang="ts">
	import { selectedNodes, SelectedDateRange, SelectedSearchQuery, SelectedCluster, unselectNodes} from "$lib/graph";
    import { ChevronRight, ChevronLeft, X } from "lucide-svelte";
    import { get, readable,writable } from 'svelte/store';
    import type { Node, Cluster } from "$lib/types";
	import { allClusters, ClustersTree } from "$lib/readcluster";


    let toShow= writable<Node[]>([])
    let abstract = writable<string>("");
    let currentPage = writable<number>(1)
    let pageCount = writable<number>(0)
  
let showMoreCluster: boolean = false;
let showMoreAbstract:boolean = false;

// Toggle function to show/hide content
    function toggleShowMoreCluster() {
        showMoreCluster = !showMoreCluster;
    }
    function toggleShowMoreAbstract(){
        showMoreAbstract = !showMoreAbstract
    }
    const handleLeftClick = () => {
        if ($currentPage != 1) currentPage.update((value) => value -1)
    }

    const handleRightClick = () => {
        if($currentPage != $pageCount) currentPage.update((value) => value +1)
    }

    const handleClearTags = () => {
        // Reverse Selection (maybe make a variable that stores the selection from the search)
        SelectedDateRange.set(undefined)
        SelectedSearchQuery.set("")
        SelectedCluster.set("")
        unselectNodes()
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

    function getClusterLabelById(cluster_id:string){
        const foundCluster = get(allClusters).find(cluster => cluster.id === cluster_id)
        if (foundCluster != undefined) return foundCluster.label

        return "error"
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

            {#if $SelectedDateRange != undefined || $SelectedSearchQuery != "" || $SelectedCluster != ""}
            <div class="filter-tags">
                {#if $SelectedDateRange != undefined}
                <div class="selected-date-range">
                    <span><b>Date:</b> {formatDateRange($SelectedDateRange)}</span>
                </div>
                {/if}

                {#if $SelectedSearchQuery != ""}
                <div class="selected-search">
                <span><b>Search:</b> {$SelectedSearchQuery}</span>
                </div>
                {/if}

                {#if $SelectedCluster != ""}
                <div class="selected-cluster">
                    <span><b>Cluster:</b> {getClusterLabelById($SelectedCluster)}</span>
                </div>

                {/if}

                <button class="clear-btn" on:click={handleClearTags}><X/></button>
            </div>
            {/if}
        <div class="info-field">
            <span class="info-field-title">title</span>
            <div class="info-field-content">{$toShow[$currentPage -1].title}</div>            
        </div>

        <div class="info-field">
            <span class="info-field-title">abstract</span>
            <div class="info-field-content {showMoreAbstract ? '' : 'collapsed'}">{$abstract}</div>
            <button class="toggle-button" on:click={toggleShowMoreAbstract}>
                {showMoreAbstract ? 'Read Less' : 'Read More'}
            </button>
        </div>

        <div class="info-field">
            <span class="info-field-title">cluster</span>
            <div class="info-field-content {showMoreCluster ? '' : 'collapsed'}">
                {getClusterInformationFromNode($toShow[$currentPage -1])}
            </div>        
            <button class="toggle-button" on:click={toggleShowMoreCluster}>
                {showMoreCluster ? 'Read Less' : 'Read More'}
            </button>
        </div>

        <div class="info-field">
            <span class="info-field-title">date</span>
            <div class="info-field-content">{$toShow[$currentPage -1].date}</div>            
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
        margin: var(--size-2);
        display: flex;
        flex-direction: column;
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
    .info-field-content.collapsed {
        overflow-y: hidden; /* Allows vertical scrolling */
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
    .filter-tags {
        display: flex;
        flex-direction: row;
        gap: var(--size-1);
    }
    .pagation-btn {
        background-color: var(--blue-8);
        height: fit-content;
        max-height: var(--size-px-1);
    }
    .selected-date-range {
        width: fit-content;
        padding: var(--size-2);
        border-radius: var(--radius-5);
        background-color: var(--blue-4);
        font-size: small;
    }
    .selected-search {
        width: fit-content;
        padding: var(--size-2);
        border-radius: var(--radius-5);
        background-color: var(--green-4);
        font-size: small;
    }
    .selected-cluster {
        width: fit-content;
        padding: var(--size-2);
        border-radius: var(--radius-5);
        background-color: var(--red-4);
        font-size: small;
    }
    .clear-btn {
        border-radius: var(--radius-6);
        max-width:fit-content;
        background-color: inherit;
        align-self: center;
    }
    .toggle-button {
        color: #0073e6;
        background-color: inherit;
        cursor: pointer;
        font-size: x-small;
        margin-top: var(--size-1);
        display: inline-block;
        align-self: left;
    }
    span {
        padding: var(--size-1);
    }
    button {
        box-shadow: none;
        border: hidden;
        text-shadow: none;
    }
    button:hover {
        box-shadow: none;
    }
    button:focus-visible {
        border:none;
        box-shadow: none;
    }
    

</style>