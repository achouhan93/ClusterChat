import { Client } from '@opensearch-project/opensearch';

import {
	OPENSEARCH_USERNAME,
	OPENSEARCH_PASSWORD,
	OPENSEARCH_INDEX,
	OPENSEARCH_NODE
} from '$env/static/private';

// // Middleware
// app.use(cors());
// app.use(express.json());

// OpenSearch client setup
const client = new Client({
	node: OPENSEARCH_NODE,
	auth: {
		username: OPENSEARCH_USERNAME,
		password: OPENSEARCH_PASSWORD
	}
});

export async function GET({ params }) {
	try {
		const response = await client.search({
			index: OPENSEARCH_INDEX,
			body: {
				query: {
					term: { id: params.id }
				}
			}
		});

		return new Response(JSON.stringify(response.body.hits.hits));
	} catch (error) {
		console.error('Error:', error);
		return new Response('Error', { status: 404 });
	}
}

// // Function to get chat completion from Groq
// async function getGroqChatCompletion(messages) {
// 	return groq.chat.completions.create({
// 		messages: messages,
// 		// Model ID for the Groq chat completion model
// 		model: 'llama3-70b-8192'
// 	});
// }

// // Route to fetch chat completion
// app.post('/api/chat-completion', async (req, res) => {
// 	try {
// 		const { message, history } = req.body;
// 		if (!message) {
// 			return res.status(400).json({ error: 'Message is required' });
// 		}

// 		// Prepare the messages array for the API call
// 		const messages = [...history, { role: 'user', content: message }];

// 		const chatCompletion = await getGroqChatCompletion(messages);
// 		res.json(chatCompletion);
// 	} catch (error) {
// 		console.error('Error fetching chat completion:', error);
// 		res.status(500).json({ error: 'Failed to fetch chat completion' });
// 	}
// });

// const PORT = API_PORT || 3001;
// app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
