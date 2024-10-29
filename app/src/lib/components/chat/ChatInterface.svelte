<script lang="ts">
	// style
	import 'open-props/buttons';
	import { Send, LoaderPinwheel, File, ChartScatter,RotateCw } from 'lucide-svelte';

	// utils
	import { splitTextIntoLines } from '$lib/utils';
	import { getSelectedNodes, document_specific } from '$lib/graph';
	import type { Node, ChatQuestion } from '$lib/types';

	// svelte
	import { writable } from 'svelte/store';
	import { afterUpdate } from 'svelte';

	// env
	//import { API_URL } from '$env/static/public';

	let isLoading = writable<boolean>(false);
	let messages = writable<{ question: string; answer: string }[]>([]);
	let TimeOutTryAgain = writable<boolean>(false);
	let payload: ChatQuestion;



	async function fetchChatAnswerWithTimeout(payload: ChatQuestion, timeout = 10000) {
	// Timeout promise that rejects after the specified time
	const timeoutPromise = new Promise<null>((_, reject) =>
		setTimeout(() => reject(new Error("Request timed out after 10 seconds")), timeout)
	);

	// Fetch request with a timeout
	const fetchPromise = (async () => {
		try {
		const response = await fetch('http://localhost:8100/ask', {
			method: 'POST',
			headers: {
			'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});
		return response.ok ? response : null;
		} catch (error) {
			console.error('Error fetching chat completion: ', error);
			return null;
		}
	})();

	// Race the fetchPromise against the timeoutPromise
	return Promise.race([fetchPromise, timeoutPromise]);
	}

	function scrollToBottom(scrollArea: HTMLDivElement) {
		// Scroll to the bottom of the message container
		scrollArea.scrollTo({
			top: scrollArea.scrollHeight,
			behavior: 'smooth'
		});
	}

	async function handleTryAgain() {
		
		try {
			TimeOutTryAgain.set(false)
			const chatCompletion = await fetchChatAnswerWithTimeout(payload);
			if (!chatCompletion) throw new Error("Failed to get chat completion");
			const fastData = await chatCompletion.json();
			const textContent = fastData.answer;
			const formattedText = splitTextIntoLines(textContent, 25);
			console.log(formattedText);
			messages.update((msgs) => {
				msgs[msgs.length - 1].answer = formattedText; // Set the answer
				return msgs;
			});
		} catch (error){
			TimeOutTryAgain.set(true)
			console.error(error)
		}

	}

	async function handleSendMessage(event: Event) {
		const form = event.currentTarget as HTMLFormElement;
		const InputMessage = new FormData(form).get('message') as string;
		$isLoading = true;

		if (!InputMessage) return;
		const formattedUserInput = splitTextIntoLines(InputMessage, 30);
		const userMessage: string = formattedUserInput;

		messages.update((msgs) => [...msgs, { question: userMessage, answer: '' }]);

		// clear input after sending message
		const chat_input = document.getElementById('chat-input') as HTMLInputElement;
		chat_input.value = '';

		// get context from selected node
		let selectedNodes: Node[] = getSelectedNodes();
		if (!selectedNodes) return
		payload = {
			question: InputMessage,
			question_type: $document_specific? "document-specific" : "corpus-based", // TODO: make it dropdown list of options
			supporting_information: selectedNodes.map((node) => (node.isClusterNode ? '' : (node.id as string)))
		};
		
		try {
			TimeOutTryAgain.set(false)
  			const chatCompletion = await fetchChatAnswerWithTimeout(payload);
  			if (!chatCompletion) throw new Error("Failed to get chat completion");

			const fastData = await chatCompletion.json();
			const textContent = fastData.answer;
			const formattedText = splitTextIntoLines(textContent, 25);
			console.log(formattedText);
			messages.update((msgs) => {
				msgs[msgs.length - 1].answer = formattedText; // Set the answer
				return msgs;
			});

		} catch (error) {
			TimeOutTryAgain.set(true)	
  			console.error(error);
			
		}

		$isLoading = false;	
	}
	afterUpdate(() => {
		// Scroll to the bottom of the message container after each update
		scrollToBottom(document.querySelector('.scroll-area') as HTMLDivElement);
	});
</script>

<div class="chat-side">
	<div class="scroll-area">
		<!-- Title that dynamically changes based on the toggle state -->
		<h4>{$document_specific ? 'Interact with Document(s)' : 'Interact with Corpus'}</h4>
		{#each $messages as message, index}
			<div class="message user">
				<p>
					{message.question}
				</p>
			</div>
			{#if message.answer === '' && !$TimeOutTryAgain}
				<div class="loader"><LoaderPinwheel size={20} /></div>

			{:else if $TimeOutTryAgain}
				<div class="try-again-message"><button on:click={handleTryAgain}>try Again <RotateCw/></button></div>
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
		<!-- Toggle for Document Specific / Corpus Specific -->
		<div class="toggle-container">
			<button class="toggle-button { $document_specific ? 'active' : '' }" on:click={() => document_specific.set(true)}>
				<File style="display:inline-block; vertical-align:middle; margin-right:5px" /> Document(s)
			</button>

			<!-- Corpus Button -->
			<button class="toggle-button { !$document_specific ? 'active' : '' }" on:click={() => document_specific.set(false)}>
				<ChartScatter style="display:inline-block; vertical-align:middle; margin-right:5px" /> Corpus
			</button>
		</div>

		<!-- Input field and send button -->
		<form on:submit|preventDefault={handleSendMessage}>
			<input
				id="chat-input"
				autocomplete="off"
				type="textarea"
				placeholder="Type your query..."
				name="message"
			/>
			<button class="btn"><Send size={18} /></button>
		</form>
	</div>
</div>

<style>
	h4 {
		color: black;
		text-align: center;
		align-self: center;
		padding: var(--size-2);
	}
	input {
		background-color: var(--surface-4-light);
		color: var(--text-2-light);
		height: var(--size-8);
		width: 100%;
	}

	.chat-side {
		background: var(--surface-3-light);
		display: grid;
		grid-template-columns: 50% 50%;
		grid-template-rows: 80% 20%;
		grid-template-areas:
			'scroll-area scroll-area'
			'input-field input-field';
		height: 100%;
		width: 100%;
	}

	.input-fields {
		display: flex;
		flex-direction: column;
		grid-area: input-field;
		align-items: center;
		height: 100%;
		width: 100%;
		padding: var(--size-2);
		background-color: var(--surface-3-light);
	}
	form {
		display: inline-flex;
		align-items: center;
		gap: var(--size-1);
		height: 100%;
		width: 100%;
		margin: var(--size-2);
		padding: var(--size-2);
	}
	button {
		border: none;
		height: var(--size-8);
		background-color: #d2f9cb;
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
		color: var(--text-2-light);
	}

	.message.user {
		align-self: flex-end;
		background-color: #fbfbfb;
	}

	.message.assistant {
		align-self: flex-start;
		background-color: #c2e2f9;
	}
	.loader {
		animation: var(--animation-spin);
		animation-duration: 2s;
		animation-timing-function: linear;
		animation-iteration-count: infinite;
		position: relative;
		max-width: fit-content;
		color: var(--surface-4-dark);
	}
	.try-again-message{
		align-self: center;
	}
	.try-again-message button {
		background-color: var(--blue-2);
		text-shadow: none;
		color: var(--text-2-light);
		font-weight: 500;
	}

	button:hover {
		box-shadow: none;
		text-shadow: none;
	}
	button {
		box-shadow: none;
		text-shadow: none;
		color: var(--text-1-dark);
	}

	.toggle-container {
		display: flex;
		align-items: center;
		gap: var(--size-2);
	}

	/* Buttons styling */
	.toggle-button {
		padding: var(--size-1);
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: #f0f0f0;
		cursor: pointer;
		font-size: 12px;
		display: flex;
		align-items: center;
		transition: background-color 0.3s ease, color 0.3s ease;
	}

	/* Highlight the active button */
	.toggle-button.active {
		background-color: #007bff;
		color: white;
		border-color: #007bff;
	}

	.toggle-button:hover {
		background-color: #0056b3;
		color: white;
	}
		
	.btn {
		padding: 10px 20px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}
</style>
