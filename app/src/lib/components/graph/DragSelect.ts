import { selectNodesInRange } from '$lib/graph';
export interface Point {
	x: number;
	y: number;
}

export class DragSelect {
	container: HTMLCanvasElement;
	selectionBox: HTMLDivElement;
	startPoint: Point | null = null;
	leftTop: Point | Point = { x: 0, y: 0 };
	bottomRight: Point | Point = { x: 0, y: 0 };

	constructor(container: HTMLCanvasElement) {
		this.container = container;
		this.selectionBox = document.createElement('div');
		this.selectionBox.classList.add('selection-box');
		this.container.appendChild(this.selectionBox);

		this.container.addEventListener('mousedown', this.onMouseDown.bind(this));
		document.addEventListener('mousemove', this.onMouseMove.bind(this));
		document.addEventListener('mouseup', this.onMouseUp.bind(this));
	}

	onMouseDown(event: MouseEvent) {
		this.startPoint = { x: event.offsetX, y: event.offsetY };
		this.selectionBox.style.left = `${this.startPoint.x}px`;
		this.selectionBox.style.top = `${this.startPoint.y}px`;
		this.selectionBox.style.width = '0px';
		this.selectionBox.style.height = '0px';
		this.selectionBox.style.display = 'block';
		this.selectionBox.ariaDisabled = 'false';
	}

	onMouseMove(event: MouseEvent) {
		if (!this.startPoint) return;

		const currentPoint = { x: event.offsetX, y: event.offsetY };
		const width = currentPoint.x - this.startPoint.x;
		const height = currentPoint.y - this.startPoint.y;

		this.leftTop.x = width < 0 ? currentPoint.x : this.startPoint.x;
		this.leftTop.y = height < 0 ? currentPoint.y : this.startPoint.y;
		this.bottomRight = {
			x: this.leftTop.x + Math.abs(width),
			y: this.leftTop.y + Math.abs(height)
		};

		this.selectionBox.style.width = `${Math.abs(width)}px`;
		this.selectionBox.style.height = `${Math.abs(height)}px`;

		if (width < 0) {
			this.selectionBox.style.left = `${currentPoint.x}px`;
		}
		if (height < 0) {
			this.selectionBox.style.top = `${currentPoint.y}px`;
		}
	}

	onMouseUp(event: MouseEvent) {
		if (!this.startPoint) return;
		selectNodesInRange([
			[this.leftTop.x, this.leftTop.y],
			[this.bottomRight.x, this.bottomRight.y]
		]);
		this.selectionBox.style.display = 'none';
	}
	destroy() {
		// Remove event listeners
		this.container.removeEventListener('mousedown', this.onMouseDown);
		this.container.removeEventListener('mousemove', this.onMouseMove);
		this.container.removeEventListener('mouseup', this.onMouseUp);

		// TODO Remove the selection box from the DOM
		if (this.selectionBox.parentNode) {
			this.selectionBox.parentNode.removeChild(this.selectionBox);
		}
		console.log('DragSelect instance destroyed');
	}
}
