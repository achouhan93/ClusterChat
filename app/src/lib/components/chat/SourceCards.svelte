<script lang="ts">
    export let title:string, source:string
    import pubmed from '$lib/assets/pubmed.png'

    function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) {
        return text;
    }
    return text.slice(0, maxLength) + "..."; // Truncate and add ellipsis
}
</script>



        <a title={title} href={source} class="card" target="_blank" rel="noopener noreferrer">
            <div class="card-index"><img class="scale-img" src={pubmed} alt=""></div>
            <div class="card-title">{truncateText(title,15)}</div>
        </a>


<style>
.card {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: baseline;      /* Center items vertically */
    padding: var(--size-1);
    max-width: 30%;
    border: 1px solid var(--blue-5);
    border-radius: 8px;
    background-color: var(--blue-2);
    cursor: pointer;
    padding: var(--size-2);
}
.card-title {
    font-size: x-small;
    font-weight: bold;
    color: #333;
    margin-left: var(--size-2);
}
/* .card-details {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #666;
        margin-top: 8px;
    } */
.card-index {
    color: var(--blue-3);
    background-color: var(--surface-2-light);
    border-radius: 50%;
    width: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    /* background-color: #f5faff; */
}
.scale-img {
    transform: scale(0.7); 
}

a {
    text-decoration: none;
}

</style>