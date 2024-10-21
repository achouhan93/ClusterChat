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
	cluster: number;
	x: number;
	y: number;
	date: Date | undefined;
};

export type Link = {
	source: string | '';
	target: string | '';
	date: Date | undefined;
};

export type ChatQuestion = {
	question:string | '';
	question_type: "document-specific" | "corpus-based";
	document_ids: string[] | [];
}