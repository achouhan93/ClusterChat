<script lang="ts">
	// style
	import 'open-props/buttons';
	import { Send, LoaderPinwheel } from 'lucide-svelte';

	// utils
	import { splitTextIntoLines } from '$lib/utils';
	import { getSelectedNodes } from '$lib/graph';
	import type { Node, ChatQuestion } from '$lib/types';

	// svelte
	import { writable } from 'svelte/store';
	import { afterUpdate } from 'svelte';

	// env
	//import { API_URL } from '$env/static/public';

	let isLoading = writable<boolean>(false);
	// let messages = writable<{ text: string; isUser: boolean }[]>([]);
	let messages = writable<{ question: string; answer: string }[]>([]);
	let context: JSON;
	

	async function searchOpenSearchById(id: string) {
		try {
			const response = await fetch(`/api/search/${id}`);
			return await response.json();
		} catch (error) {
			console.error('Error fetching data: ', error);
			return null;
		}
	}

	async function fetchChatCompletion(payload: string) {
		try {
			const response = await fetch('/api/chat-completion', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: payload
			});
			return response;
		} catch (error) {
			console.error('Error fetching chat completion: ', error);
			return null;
		}
	}

	
	async function fetchChatAnswer(payload: ChatQuestion){
		/* Requests FastAPI and fetches the answer to the question w/o context */
		try {
			const response = await fetch("http://localhost:8100/ask", {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)

			});
			return response;
		} catch (error) {
			console.error('Error fetching chat completion: ', error);
			return null;
		}
	}

	function scrollToBottom(scrollArea: HTMLDivElement) {
		// Scroll to the bottom of the message container
		scrollArea.scrollTo({
			top: scrollArea.scrollHeight,
			behavior: 'smooth'
		});
	}

	async function handleSendMessage(event: Event) {
		console.log(event.target)
		const form = event.currentTarget;
		const message = new FormData(form).get('message') as string;
        $isLoading = true;
		

		if (!message) return;
		const formattedUserInput = splitTextIntoLines(message, 30);
		const userMessage: string = formattedUserInput;

		messages.update((msgs) => [...msgs, { question:userMessage, answer: '' }]);

		// clear input after sending message
		const chat_input = document.getElementById('chat-input') as HTMLInputElement;
		chat_input.value = '';

		// get context from selected node
		let selectedNodes: Node[] = getSelectedNodes();

		let payload:ChatQuestion = {
			question: userMessage,
			question_type: "document-specific", // TODO: make it dropdown list of options
			document_ids:  selectedNodes.map(node => (node.id as string))
		}
		// fetch chat completion from groq api
		const chatCompletion = await fetchChatAnswer(payload);
		if (!chatCompletion) throw new Error('Failed to get chat completion');

		const fastData = await chatCompletion.json();
		const textContent = fastData.answer
		const formattedText = splitTextIntoLines(textContent, 25);
		console.log(formattedText)
		// messages.update((msgs) => [
		// 	...msgs,
		// 	{ question: userMessage, answer: formattedText },
		// ]);

		messages.update((msgs) => {
        msgs[msgs.length - 1].answer = formattedText // Set the answer
        return msgs;
      });

        $isLoading = false;
		// scroll to bottom
	}
	afterUpdate(() => {
		// Scroll to the bottom of the message container after each update
		scrollToBottom(document.querySelector('.scroll-area') as HTMLDivElement);
	});

</script>

<div class="chat-side">
	<div class="scroll-area">
		{#each $messages as message, index}
				<div class="message user">
					<p>
						{message.question}
					</p>
				</div>
				{#if message.answer===""}
					<div class="loader"><LoaderPinwheel size={20}/></div>
				{:else}
				<div class="message assistant">
					<p>
						{message.answer}
					</p>
				</div>
				{/if}
		{/each}
	</div>
	<div class="input-fields">
		<form on:submit|preventDefault={handleSendMessage}>
			<input
				id="chat-input"
				autocomplete="off"
				type="textarea"
				placeholder="Type a message..."
				name="message"
				on:keypress={(e) => e.key === 'Enter' && handleSendMessage(e)}
			/>
			<button class="btn"><Send size={18} /></button>
		</form>
	</div>
</div>

<style>
	input {
		background-color: var(--surface-4-light);
		color: var(--text-2-light);
		height: var(--size-8);
	}

	.chat-side {
		background: var(--surface-3-light);
		display: grid;
		grid-template-columns: 50% 50%;
		grid-template-rows: 85% 15%;
		grid-template-areas:
			'scroll-area scroll-area'
			'input-field input-field';
		height: 100%;
		width: 100%;
	}

	.input-fields {
		display: flex;
		flex-direction: row;
		grid-area: input-field;
		justify-content: space-around;
		align-items: center;
		height: 100%;
	}
	form {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		height: 100%;
	}
	button {
		border: none;
		height: var(--size-8);
		background-color: var(--brand-whatsapp);
		box-shadow: none;
	}

	.scroll-area {
		height: 100%;
		grid-area: scroll-area;
		/* Control the overflow behavior */
		overflow-y: auto; /* Allows vertical scrolling */
		overflow-x: hidden; /* Prevents horizontal scrolling */

		padding: var(--size-4);
		display: flex;
		flex-flow: column;
	}

	.message {
		display: flex;
		flex-direction: column;
		font-size: (--size-2);
		max-width: 80%;
		border-radius: var(--size-4);
		padding: var(--size-3);
		margin-bottom: var(--size-3);
	}

	.message.user {
		align-self: flex-end;
		background-color: #248bf5;
	}

	.message.assistant {
		align-self: flex-start;
		background-color: var(--surface-2-dark);
	}
    .loader {
        animation: var(--animation-spin);
		animation-duration: 2s;
		animation-timing-function: linear;
		animation-iteration-count: infinite;
        position: relative;
        max-width: fit-content;
    }
</style>
