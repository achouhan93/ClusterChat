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
	cluster: string;
	isClusterNode: boolean | false;
	x: number;
	y: number;
	date: Date | number | undefined;
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
	question_type: 'document-specific' | 'corpus-specific';
	supporting_information: string[] | [];
};

export type Source = {
	id: string 
	title:string
}
