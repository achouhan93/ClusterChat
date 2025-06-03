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

export type Point = {
	id: string;
	title: string | 'No Title';
	cluster: string;
	x: number;
	y: number;
	date: Date | number | undefined;
}

export type Cluster = {
	id: string;
	xCenter: number;
	yCenter: number;
	label: string | '';
	depth: number | 0;
	isLeaf: boolean | false;
	path: string;
};

export const undefinedCluster: Cluster = {
	id: '',
	xCenter: 0,
	yCenter: 0,
	label: '',
	depth: 0,
	isLeaf: false,
	path: ''
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
	id: string;
	title: string;
};

export type InfoPanel = {
	pubmed_id: string | '';
	title: string;
	abstract: string;
	date: Date | number | undefined;
	cluster_top: string[];
	authors_name: string[];
	journal_title: string;
	keywords: string[];
};
