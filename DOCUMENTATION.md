
## Folder Structure


### Taken from AP and not changed

- [`transfer/`](transfer/README.md): Scripts for pushing and pulling the data to and from OpenSearch.
- [`embed/`](embed/README.md): Scripts for generating embeddings for arXiv papers.
- [`cluster/`](cluster/README.md): Scripts and data for clustering analysis.
- [`analysis/`](analysis/README.md): Contains Jupyter notebooks for various analyses.

### Newly created or adapted

- [`app/`](app/README.md): Frontend application built with Sveltekit.

## Setup
### Create `.env` file

You can find a `.env.example` file with the structure needed for the environment file. DO NOT delete the comments `#Public` and `#Private` since they are essential for the file to work correctly.

### Install npm packages and run the app
```bash
cd app
npm install 
npm run dev
```

