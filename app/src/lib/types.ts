// export type Node = {
// 	id: string;
// 	cluster: number;
// 	x: number;
// 	y: number;
// 	color: string;
// 	size: number;
// 	title: string;
// 	date: Date | undefined;
// };

export type Node = {
	id: string;
	title: string | 'No Title';
	cluster: number;
	isClusterNode: boolean | false;
	x: number;
	y: number;
	date: Date | undefined;
	color: string | '#000';
};

export type Cluster = {
	id: string;
	xCenter: number;
	yCenter: number;
	label: string | '';
	depth: number | 0;
	isLeaf: boolean | false;
	path: string;
};

export type Link = {
	source: string | '';
	target: string | '';
	date: Date | undefined;
};

export type ChatQuestion = {
	question: string | '';
	question_type: 'document-specific' | 'corpus-based';
	document_ids: string[] | [];
};
