export type Node = {
	id: string;
	cluster: number;
	x: number;
	y: number;
	color: string;
	size: number;
	title: string;
	date: Date | undefined;
};

export type Link = {
	source: string | '';
	target: string | '';
	date: Date | undefined;
};
