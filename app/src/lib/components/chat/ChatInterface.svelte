<script lang="ts">
	// style
	import 'open-props/buttons';
	import { Send, LoaderPinwheel } from 'lucide-svelte';

	// utils
	import { splitTextIntoLines } from '$lib/utils';
	import { getSelectedNodes } from '$lib/graph';
	import type { Node } from '$lib/types';

	// svelte
	import { writable } from 'svelte/store';
	import { afterUpdate } from 'svelte';


	let isLoading = writable<boolean>(false);
	let messages = writable<{ text: string; isUser: boolean }[]>([]);
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
	function scrollToBottom(scrollArea: HTMLDivElement) {
		// Scroll to the bottom of the message container
		scrollArea.scrollTo({
			top: scrollArea.scrollHeight,
			behavior: 'smooth'
		});
	}

	async function handleSendMessage(event: Event) {
		const form = event.target as HTMLFormElement;
		const message = new FormData(form).get('message') as string;
        $isLoading = true;

		// clear input after sending message
		const chat_input = document.getElementById('chat-input') as HTMLInputElement;
		chat_input.value = '';

		if (!message) return;
		const formattedUserInput = splitTextIntoLines(message, 30);
		const userMessage: string = formattedUserInput;

		// get context from selected node
		let selectedNodes: Node[] = getSelectedNodes();
		if (selectedNodes.length > 0) {

			// fetch response for the first node TODO: multiple nodes
			const apiResponse = (await searchOpenSearchById(selectedNodes[0].id)) as JSON;
			if (!apiResponse) {
				throw new Error('Failed to fetch node');
			}
			context = apiResponse;
			//console.dir('API Response:', JSON.stringify(context, null, 2));
		} else {
			throw new Error('No Node was selected');
		}

		// Prepare history
		const history = [];
		$messages.slice(-6).forEach((msg) => {
			history.push({
				role: msg.isUser ? 'user' : 'assistant',
				content: msg.text
			});
		});
		history.push({ role: 'user', content: formattedUserInput });

		// Format the context
		const fullContext = `${context ? `${JSON.stringify(context[0]._source.abstract)}\n\n` : ''}`;
		// ${history.map((msg) => `${msg.role}: ${msg.content}`).join('\n')}`;
		//console.dir(fullContext);

		// Construct the payload
		const payload = {
			context: fullContext || null, // include context if it exists
			messages: history
		};

		let payloadString = JSON.stringify(payload);

		// Log the payload for verification
		//console.log('Payload:', JSON.stringify(payload, null, 2));

		// fetch chat completion from groq api
		const chatCompletion = await fetchChatCompletion(payloadString);
		if (!chatCompletion) throw new Error('Failed to get chat completion');

		const groqData = await chatCompletion.json();
		const textContent = groqData.choices[0]?.message?.content || '';
		const formattedText = splitTextIntoLines(textContent, 25);
		messages.update((msgs) => [
			...msgs,
			{ text: userMessage, isUser: true },
			{ text: formattedText, isUser: false }
		]);

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
			{#if message.isUser}
				<div class="message user">
					<p>
						{message.text}
					</p>
				</div>
			{:else}
				<div class="message assistant">
					<p>
						{message.text}
					</p>
				</div>
			{/if}
		{/each}
        {#if $isLoading}
            <div class="loader"><LoaderPinwheel size={20}/></div>
        {/if}
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
		background-color: var(--surface-4-dark);
		height: 2rem;
	}

	.chat-side {
		background: var(--background-dark);
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
