import * as d3 from 'd3';  // Make sure to install and import d3 properly
import { selectNodesInRange, INITIAL_FITVIEW } from '$lib/graph';
import type { Node } from '$lib/types';


export function dragSelection(c1:HTMLCanvasElement) {

  const ctx1 = c1.getContext("2d") as CanvasRenderingContext2D;
  

  
  const drawSelection = (e) => {
    ctx1.strokeStyle = "#000";
    ctx1.beginPath();
    ctx1.rect(origin.x, origin.y, e.offsetX - origin.x, e.offsetY - origin.y); 
    ctx1.stroke();
  };
  
  const clear = () => {
    ctx1.strokeStyle = "#fff";
    ctx1.clearRect(0, 0, c1.width, c1.height);
  };
  
  const render = (e) => {
    clear();
    
    if (origin) drawSelection(e);
  }
  
  window.onload = drawImage;
  
  let origin = null;
  c1.onmousedown = e => { origin = {x: e.offsetX, y: e.offsetY}; };
  c1.onmouseup = e => { origin = null; render(e); };
  c1.onmousemove = render;

} 

  