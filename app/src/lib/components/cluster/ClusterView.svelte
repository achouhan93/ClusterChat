<script>
    import { ClustersTree, allClusters } from "$lib/readcluster";
    import { get } from "svelte/store";
    import { dataloaded } from "$lib/readcluster";
    async function handleClick(){
        // retrieve cluster by label und find id,path etc.
        // query opensearch to get all the document ids that are in that and "select them"
        

        
    }
</script>
<div class="cluster-scroll">
    <ul>
        {#if get(allClusters)}
        {#each get(allClusters) as cluster }
        {#if cluster.depth === 4}
            <button on:click={handleClick()}><li>[{cluster.id}]{cluster.label}</li></button>
        {/if}
        {/each}
        {/if}
    </ul>
</div>



<style>
    .cluster-scroll{
        display: flex;
        justify-content: right;
        background-color: rgb(255, 255, 255);
        opacity: 100%;
    }
    ul {
		list-style-type: none;
	}

    button {
        background-color: rgb(255, 255, 255);
        opacity: 100%;
        border: none;
        font-size: var(--font-size-1);
        box-shadow: none;
    }
    button li {
        font-size: 12px;
        font-weight: var(--font-weight-2);
        

    }
    button::hover{
        box-shadow: none;
    }

</style>