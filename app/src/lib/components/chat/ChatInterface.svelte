<script lang="ts">
	// style
	import 'open-props/buttons';
	import 'open-props/style';
	import 'open-props/normalize';
	import {
		Send,
		LoaderPinwheel,
		File,
		ChartScatter,
		RotateCw,
		Sparkle,
		Trash2
	} from 'lucide-svelte';

	// utils
	import { splitTextIntoLines } from '$lib/utils';
	import { getSelectedNodes } from '$lib/graph';
	import { document_specific } from '$lib/stores/uiStore';
	import type { Node, ChatQuestion, Source } from '$lib/types';
	import SourceCards from './SourceCards.svelte';

	// svelte
	import { get, writable } from 'svelte/store';
	import { afterUpdate } from 'svelte';
	import type { integer } from '@opensearch-project/opensearch/api/types';

	// env
	//import { API_URL } from '$env/static/public';

	let isLoading = writable<boolean>(false);
	let messages = writable<{ question: string; answer: string; sources: string[] }[]>([]);
	let TimeOutTryAgain = writable<boolean>(false);
	let currentFoundSources = writable<Source[]>([]);
	let payload: ChatQuestion;

	async function fetchSourceInfo(doc_ids: string[]) {
		const response = await fetch('/api/opensearch/findtitle', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},

			body: JSON.stringify({ doc_ids }) // Send the array in the request body as JSON
		});
		const data = await response.json();
		const foundSources: Source[] = data.map(
			(item) =>
				({
					id: item._source.document_id,
					title: item._source.title
				}) satisfies Source
		);
		currentFoundSources.set(foundSources);
	}



		async function fetchChatAnswerWithTimeout(payload: ChatQuestion, timeout = 15000) {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), timeout);
		let payloadRequest = payload
		payloadRequest.supporting_information=  payload.supporting_information.map(item => String(item));
		try {
			const response = await fetch('/api/ask', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload),
			});

			clearTimeout(timeoutId);

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.message || `Request failed with status ${response.status}`);
			}

			return response
    } catch (error:any) {
        clearTimeout(timeoutId);
        console.error('API request error:', error);
        throw error;
    }
}



	function scrollToBottom(scrollArea: HTMLDivElement) {
		// Scroll to the bottom of the message container
		scrollArea.scrollTo({
			top: scrollArea.scrollHeight,
			behavior: 'smooth'
		});
	}

	async function handleClearChat() {
		messages.set([]);
	}

	async function handleTryAgain() {
		try {
			TimeOutTryAgain.set(false);
			const chatCompletion = await fetchChatAnswerWithTimeout(payload);
			if (!chatCompletion) throw new Error('Failed to get chat completion');
			const fastData = await chatCompletion.json();
			const textContent = fastData.answer;
			const formattedText = splitTextIntoLines(textContent, 25);
			// if(fastData.sources.length != 0) fetchSourceInfo(fastData.sources)
			// else currentFoundSources.set([])
			messages.update((msgs) => {
				msgs[msgs.length - 1].answer = formattedText; // Set the answer
				msgs[msgs.length - 1].sources =
					fastData.sources.length != 0 && get(document_specific)
						? fastData.sources.slice(0, 3)
						: [];
				return msgs;
			});
		} catch (error) {
			TimeOutTryAgain.set(true);
			console.error(error);
		}
	}

	async function handleSendMessage(event: Event) {
		const form = event.currentTarget as HTMLFormElement;
		const InputMessage = new FormData(form).get('message') as string;
		$isLoading = true;

		if (!InputMessage) return;
		const formattedUserInput = splitTextIntoLines(InputMessage, 30);
		const userMessage: string = formattedUserInput;

		messages.update((msgs) => [...msgs, { question: userMessage, answer: '', sources: [] }]);

		// clear input after sending message
		const chat_input = document.getElementById('chat-input') as HTMLInputElement;
		chat_input.value = '';

		// get context from selected node
		let selectedNodes: Node[] = getSelectedNodes();
		if (!selectedNodes) return;
		payload = {
			question: InputMessage,
			question_type: $document_specific ? 'document-specific' : 'corpus-specific', // TODO: make it dropdown list of options
			supporting_information: selectedNodes.map((node) =>
				node.isClusterNode ? '' : (node.id)
			)
		};

		try {
			TimeOutTryAgain.set(false);
			const chatCompletion = await fetchChatAnswerWithTimeout(payload);
			if (!chatCompletion) throw new Error('Failed to get chat completion');

			const fastData = await chatCompletion.json();
			const textContent = fastData.answer;
			const formattedText = splitTextIntoLines(textContent, 25);
			// if(fastData.sources.length != 0) fetchSourceInfo(fastData.sources)
			// else currentFoundSources.set([])
			messages.update((msgs) => {
				msgs[msgs.length - 1].answer = formattedText; // Set the answer
				msgs[msgs.length - 1].sources =
					fastData.sources.length != 0 && get(document_specific)
						? fastData.sources.slice(0, 3)
						: [];
				return msgs;
			});
		} catch (error) {
			TimeOutTryAgain.set(true);
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
		<div class="scroll-area-header">
			<h4>{$document_specific ? 'Interact with Document(s)' : 'Interact with Corpus'}</h4>
			<button
				class="menu-button"
				aria-label="Options"
				on:click|stopPropagation={handleClearChat}
				title="Clear Chat"><Trash2 /></button
			>
		</div>

		{#each $messages as message, index}
			<div class="message user">
				<p>
					{message.question}
				</p>
			</div>
			{#if message.answer === '' && !$TimeOutTryAgain && index === $messages.length - 1}
				<div class="loader"><LoaderPinwheel size={20} /></div>
			{:else if $TimeOutTryAgain && index === $messages.length - 1}
				<div class="try-again-message">
					<button on:click={handleTryAgain}>Try Again <RotateCw /></button>
				</div>
			{:else}
				<div class="message assistant">
					<p>
						{message.answer}
					</p>
					{#if message.sources.length != 0}
						<div class="sources-list">
							{#each message.sources as doc_source}
								<SourceCards
									title={doc_source}
									source={`https://pubmed.ncbi.nlm.nih.gov/${doc_source}`}
								/>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		{/each}
	</div>
	<div class="input-fields">
		<!-- Toggle for Document Specific / Corpus Specific -->
		<div class="toggle-container">
			<button
				class="toggle-button {$document_specific ? 'active' : ''}"
				on:click={() => document_specific.set(true)}
			>
				<File style="display:inline-block; vertical-align:middle; margin-right:5px" /> Document(s)
			</button>

			<!-- Corpus Button -->
			<button
				class="toggle-button {!$document_specific ? 'active' : ''}"
				on:click={() => document_specific.set(false)}
			>
				<ChartScatter style="display:inline-block; vertical-align:middle; margin-right:5px" /> Corpus
			</button>
		</div>

		<!-- Input field and send button -->
		<form on:submit|preventDefault={handleSendMessage}>
			<!--Feature on Hold-->
			<!-- <button type="button" class="chat-model-btn" title='Choose Model'
			><Sparkle size={20}/></button
			> -->
			<!-- <select name="model-accessor" id="model-accessor">
				<option value="mixtral">Mixtral</option>
				<option value="openai">OpenAI</option>
			</select> -->

			<input
				id="chat-input"
				autocomplete="off"
				type="textarea"
				placeholder="Type your query..."
				name="message"
			/>
			<button class="send-btn"><Send size={18} /></button>
		</form>
	</div>
</div>

<style>
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
		animation: fade-in 300ms var(--ease-2);
	}

	.input-fields {
		display: flex;
		flex-direction: column;
		grid-area: input-field;
		align-items: center;
		justify-content: flex-end;
		height: 100%;
		width: 100%;
		padding: var(--size-2);
		background-color: var(--surface-3-light);
		z-index: 3;
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

	#chat-input:hover {
		cursor: text;
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

	.scroll-area-header {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		align-items: center;
	}

	.scroll-area-header h4 {
		grid-column: 2;
		text-align: center;
	}

	.scroll-area-header button {
		grid-column: 3;
		justify-self: end;
	}
	.menu-button {
		background: none;
		border: none;
		font-size: var(--size-4);
		cursor: pointer;
		padding: var(--size-1);
		border-radius: 4px;
		transition: background-color 0.3s ease;
	}

	.menu-button:hover {
		background-color: var(--surface-4-light);
	}
	.menu-button:active {
		background-color: var(--gray-5);
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
	.try-again-message {
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
	}

	.toggle-container {
		display: flex;
		align-items: center;
		gap: var(--size-2);
	}

	/* Buttons styling */
	.toggle-button {
		padding: var(--size-4);
		border: 1px solid #ccc;
		border-radius: 4px;
		background-color: #f0f0f0;
		cursor: pointer;
		font-size: 12px;
		display: flex;
		align-items: center;
		transition:
			background-color 0.3s ease,
			color 0.3s ease;
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

	.send-btn {
		padding: 10px 20px;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}
	.sources-list {
		margin-top: var(--size-3);
		display: inline-flex;
		flex-direction: row;
		gap: var(--size-2);
		flex-wrap: nowrap;
	}
	/* #model-accessor {
		background-color: var(--blue-4);
		color: var(--gray-0);
		width: fit-content;
	} */
	/* .chat-model-btn {
		background-color: var(--blue-4);
		color: var(--gray-0);
		width: fit-content;
	} */
</style>
