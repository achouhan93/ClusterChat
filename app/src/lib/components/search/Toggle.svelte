
<script lang="ts">
  import { writable } from 'svelte/store';

  export let button_id:string; export let label_1:string; export let label_2:string; export let name:string;
  export let form:string;
  
  let checked=false;

</script>
<input form={form} type="hidden" name={name} value={checked ? label_2 : label_1 }>
<input type="checkbox" id={button_id} class="toggleCheckbox" bind:checked={checked} 
/>
<label for={button_id} class='toggleContainer'>
  <div>{label_1}</div>   
  <div>{label_2}</div>
</label>


  <style>

.toggleContainer {
   position: relative;
   display: grid;
   grid-template-columns: repeat(2, 1fr);
   width: max-content;
   border: 1px solid #f0f0f0;
   border-radius: 20px;
   /* background: #343434; */
   background: white;
   font-weight: bold;
   font-size: small;
   color: #343434;
   cursor: pointer;
   margin: var(--size-px-1);
   width: 100%;
 }
 .toggleContainer::before {
   content: '';
   position: absolute;
   width: 50%;
   height: 100%;
   left: 0%;
   border-radius:20px;
   background: #007bff;
   transition: all 0.3s;
 }
 .toggleCheckbox:checked + .toggleContainer::before {
    left: 50%;
 }
 .toggleContainer div {
   padding: 6px;
   text-align: center;
   z-index: 1;
 }
 .toggleCheckbox {
   display: none;
 }
 .toggleCheckbox:checked + .toggleContainer div:first-child{
   color: var(--text-2-light);
   transition: color 0.3s;
 }
 .toggleCheckbox:checked + .toggleContainer div:last-child{
   color: white;
   transition: color 0.3s;
 }
 .toggleCheckbox + .toggleContainer div:first-child{
   color: white;
   transition: color 0.3s;
 }
 .toggleCheckbox + .toggleContainer div:last-child{
   color: var(--text-2-light);
   transition: color 0.3s;
 }
  </style>
