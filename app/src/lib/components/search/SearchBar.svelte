<script lang=ts>
import { Search } from "lucide-svelte";

async function handleSearch(event: Event){
    console.log(event.target)
}
</script>
<div class="search-bar-elems">
    <input 
    id="search-bar-input"
    autocomplete="off"
    type="textarea"
    placeholder="search..."
    name="search-query"
    on:keypress={(e) => e.key === 'Enter' && handleSearch(e)}
/>
<div class="dropdown">
    <select name="search" id="search-accessor">
        <option value="id">ID</option>
        <option value="title">Title</option>
        <option value="abstract">Abstract</option>
      </select>
      
</div>
</div>

<style>
    .search-bar-elems{
        display: flex;
        direction: rows;
        margin-top: var(--size-3);

    }
    input {
        
        width: 80%;
        background-color: var(--surface-2-light);
        color: var(--text-2-light);
        transition: none !important;
        margin-left: var(--size-2);
        padding: var(--size-3);

    }
    input:focus-visible {
         transition: none !important;
    }
    #search-accessor {
        background-color: var(--surface-2-light);
        color: var(--text-1-light);
        height: 100%;
        margin-left: var(--size-2);
        border-radius: var(--size-3);
        background-color: var(--blue-2);
        padding: var(--size-1);
    }

</style>