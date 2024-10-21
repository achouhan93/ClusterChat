import { GROQ_API_KEY } from '$env/static/private';
import { Groq } from 'groq-sdk';
const groq = new Groq({ apiKey: GROQ_API_KEY });

// Function to get chat completion from Groq
// async function getGroqChatCompletion(messages: any[]) {
// 	return groq.chat.completions.create({
// 		messages: messages,
// 		// Model ID for the Groq chat completion model
// 		model: 'llama3-70b-8192'
// 	});
// }

export async function POST({ request }) {
	const { context, messages } = await request.json();

	// TODO: fetch context, have history add a user and fetch the completion
	try {
		if (!context || !messages) {
			return new Response('Message is required!', { status: 400 });
		}

		// TEST only
		//return new Response(JSON.stringify(messages), {status:418})

		// prepare messages array for API call
		const chat = [
			...messages,
			{
				role: 'system',
				content: `Use the following context for your answer and be short, clear and precise in your response. ${context}`
			}
		];

		// const chatCompletion = await getGroqChatCompletion(chat);
		// return new Response(JSON.stringify(chatCompletion), {
		// 	headers: {
		// 		'Content-Type': 'application/json'
		// 	}
		// });
	} catch (error) {
		return new Response('Error fetching chat completion', { status: 400 });
	}
}
