
# App Structure
```bash
.
├── eslint.config.js
├── package.json
├── package-lock.json
├── postcss.config.js
├── README.md
├── src                               <-- Source file
│   ├── app.css
│   ├── app.d.ts
│   ├── app.html
│   ├── data
│   │   └── nodes.csv
│   ├── lib
│   │   ├── components
│   │   │   ├── chat
│   │   │   │   └── ChatInterface.svelte  <-- RAGChat lives here
│   │   │   └── graph
│   │   │       └── DragSelect.ts
│   │   ├── graph.ts                <-- Graph, Timeline and Searchbar
│   │   ├── index.ts
│   │   ├── readcluster.ts          <-- Reads Nodes from .csv
│   │   ├── types.ts                <-- Type Definitions (Node, Link)
│   │   └── utils.ts
│   └── routes          
│       ├── api                     <-- API Endpoints
│       │   ├── chat-completion
│       │   │   └── +server.ts
│       │   ├── opensearch
│       │   │   └── [size]
│       │   │       └── +server.ts
│       │   └── search
│       │       └── [id]
│       │           └── +server.ts
│       └── +page.svelte            <-- Main page
├── static
│   └── favicon.png
├── svelte.config.js
├── tsconfig.json
└── vite.config.ts
```


## Root File
The root file holds the configuration files to the used tools mentioned below. The most important configurations are the `svelte.config.js` and `tsconfig.json` for TypeScript configuration (where we specified that JavaScript files are allowed).
# Tools used
## For Implementation
- [TypeScript](https://www.typescriptlang.org/)
- SvelteKit
## Code Structure
- [Prettier](https://prettier.io/) for formatting the code and making it easier to read. Activate by running `npm run format`
- [EsLint](https://eslint.org/) for static analysis and error finding
## Styling
- [OpenProps](https://open-props.style/) which is plain css with variables and was used for minimal space and performance


# Implementing the Graph

The graph shown on the canvas is created with the `createGraph()` function. This function gets `div#main-graph` specified in `+page.svelte` and uses it as the canvas for the `Cosmograph` class. This class also takes a Configuration variable `GraphConfig`. The configuration variable contains all different parameters to change the appearance and behavior of the graph. Notice that the Event Listeners also get specified in the config variable with a number of preset Event Listeners defined in the type `CosmographInputConfig<Node,Link>`. 

The Search bar and the Timeline follows a similar pattern as the graph. In the `SearchConfig` variable the accessors specify which node parameters can be used for lexical search. Here also there is a list of Event Listeners to choose from. In the timeline accessor you will find `12 / 12 / 2000` as a fallback date, just to catch any nodes without dates or errors. It can be of course removed.  Notice that the timeline needs to take in a `castedGraph` since it doesn't work with my defined types int `types.ts`. That however, doesn't prove any issues in performance. 


## Control buttons

We have three control buttons on the bottom right side for multiple selection, rectangular selection and fitting the view (in that order). 

*The rectangular selection remains buggy and will be elivated once the update for @cosmograph/cosmograph releases*

When one of the buttons gets clicked it triggers a toggle in the boolean and allows the event listeners in the configurations to act accordingly. Here is an example for the boolean `selectMultipleNodes`
```typescript
export let selectMultipleNodes: boolean = false;

// ...

	onClick(clickedNode) {
		handleNodeClick(clickedNode as Node);
	},

// ...

export function toggleMultipleNodesMode() {
	selectMultipleNodes = !selectMultipleNodes;
}

// ...

const handleNodeClick = async (clickedNode: Node) => {
	if (!selectMultipleNodes && clickedNode) {
        // ... 
    }
};
```
The other control buttons follow the same pattern. For the rectangular selection we created the class `DragSelect()` specified in the `DragSelect.ts` file.

## Actions on graph

Instead of exporting the whole graph we defined multiple functions for the functionalities needed. All the possible functionalities are specified in the cosmograph documentation [here](https://cosmograph.app/docs/cosmograph/Cosmograph%20Library/Cosmograph#rendering-preferences).

List of the adapted functions:

- `updateGraph` updates the configuration of the graph to change appearance based on actions of the user
- `selectNodesInRange` selects nodes in a range from left top to bottom right. Useful for rectangular selection.
- `unselectNodes` unselects nodes and removes them from the `selectedNodes` array and removes the labels for them.
- `getSelectedNodes` returns the array `selectedNodes`
- `fitViewofGraph` centers the graph and makes is fit the window of the user.
- `showLabelsfor` specifies which nodes get labels shown for and updates the graph accordingly

# API Endpoints in Sveltekit
Sveltekit offers an implementation of a server directly in the `/routes` folder using a `server.ts` files to handle the Requests as specified [here](https://kit.svelte.dev/docs/routing#server). We created three different Endpoints with different parameters which are specified by the folder names with a square bracket.
-  `/api/search/[id]` handles `GET` requests and returns the document with the specified id from opensearch
- `/api/chat-completion` handles `POST` requests and interacts with Groq to get the chat completion of each message sent by the user from the [chat interface](#chat-interface). To change the prompt sent to Groq edit the `+server.ts` file in this path.
- `opensearch/[size]` is an endpoint for getting `[size]`-documents from opensearch to avoid getting the data from .csv files. 

# Chat Interface

This svelte components handles all the messaging. The functions `searchOpenSearchById` and `fetchChatCompletion` simply send requests to the respective [API Endpoints](#api-endpoints-in-sveltekit) explained above. When `handleSendMessage` gets called it gets the user input and stores it in `userMessage` and gets the selected node by the user (only one for now). The function fetches context on that node from opensearch using `searchOpenSearchById`. The context gets then formatted to be sent via `POST` to Groq and receive the message completion. 

Every message has the type `{ text: string; isUser: boolean }` and after each sent and received message the `messages` writeable gets updated. To keep the app reactive we chose to use [svelte stores](https://svelte.dev/docs/svelte-store), which provide reactive functions like `writeable` that holds it's data and updates it in the user's session.


