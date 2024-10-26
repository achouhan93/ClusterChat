<script lang="ts">
	import { selectedNodes } from "$lib/graph";
    import { allClusters } from "$lib/readcluster";
    import { get } from 'svelte/store';

    let toShow:Node[] = []
    let toShowAbstract:string = "";

   async function fetchAbstractById(id:string){
        const response = await fetch(`/api/opensearch/findabstract/${id}`)
        const data = await response.json()
        return data
    }
    async function getAbstractById(id:string){
        return await fetchAbstractById(id)
    }

    selectedNodes.subscribe(nodes =>{
        toShow = nodes
    })




    
</script>

<div class="node-information-view">
    <h4>Node Information</h4>
    <div class="node-info-list">
        {#if toShow.length != 0}

        <div class="info-field">
            <span class="info-field-title">title</span>
            <div class="info-field-content">{toShow[0].title}</div>            
        </div>

        <div class="info-field">
            <span class="info-field-title">id</span>
            <div class="info-field-content">{toShow[0].id}</div>            
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
    .info-field {
        margin: --var(--size-4);
    }
    .info-field-title {
        color: var(--blue-8);
        font-weight: var(--font-weight-8);
        padding: var(--size-2)
    }
    .info-field-content{
        height: fit-content;
        font-size: var(--font-size-1);
        padding: var(--size-2);
        color: var(--text-1-light);
        background-color: var(--surface-4-light);
    }

</style>