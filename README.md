# Open Science Knowledge Graph of 30 Research Papers
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/1250590334.svg)](https://doi.org/10.5281/zenodo.20402223)

This project builds a reproducible and FAIR pipeline to analyze **30 open-access research papers** and turn the results into an **RDF Knowledge Graph** that can be queried with SPARQL. 

### Documentation server

The project documentation is available in the `docs/` folder and can be served with MkDocs.

If the `docs` service is enabled in `docker-compose.yml`, start it with:

```bash
docker compose up docs
```

Then open the documentation site at:

```text
http://localhost:8000
```

## Overview

The pipeline:

1. parses PDFs with **Grobid**;
2. extracts abstracts and acknowledgements;
3. identifies topics using **BERTopic + KMeans**;
4. computes paper similarity with **MiniLM embeddings + cosine similarity**;
5. extracts people, organizations and grants from acknowledgements;
6. builds an **RDF/Turtle Knowledge Graph**;
7. records provenance with **PROV-O**;
8. packages the project as an **RO-Crate**.

## Workflow

```text
parse → abstracts → acknowledgements → topics → similarity
      → ner → grants → evaluate → enrich → kg → prov → rocrate
```

The `enrich` step adds external information from **OpenAlex** and **Wikidata/ROR**.

## Repository structure

| Folder / file                      | Purpose                                       |
| ---------------------------------- | --------------------------------------------- |
| `config/`                          | Configuration and parameters                  |
| `data/`                            | Papers, metadata and validation data          |
| `docs/`                            | Documentation, validation and model decisions |
| `ontology/`                        | `oskg` ontology                               |
| `provenance/`                      | PROV-O trace and summary                      |
| `queries/`                         | SPARQL queries                                |
| `results/`                         | Pipeline outputs                              |
| `figures/`                         | Generated plots                               |
| `ro-crate/`                        | RO-Crate metadata                             |
| `src/`                             | Pipeline code                                 |
| `tests/`                           | Test suite                                    |
| `Dockerfile`, `docker-compose.yml` | Container setup                               |

## Installation

Requires **Python 3.10+** and a running **Grobid** server.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start Grobid:

```bash
docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.1
```

Run the pipeline:

```bash
python -m src.pipeline --config config/config.yaml
python -m src.pipeline --steps topics,similarity,kg
python -m src.pipeline --skip parse
```
## Installation with Docker Compose

Docker Compose builds the project image, installs the dependencies and starts the required services.

```bash
docker compose up --build pipeline
```

Useful commands:

```bash
docker compose up pipeline      # run pipeline
docker compose up fuseki        # optional SPARQL server
docker compose down             # stop services
```

| Service | Purpose | Port |
|---|---|---|
| `pipeline` | Runs the project pipeline | — |
| `grobid` | PDF parsing | `8070` |
| `fuseki` | Optional SPARQL querying | `3030` |



## Main outputs

| File                                    | Description                        |
| --------------------------------------- | ---------------------------------- |
| `results/abstracts.json`                | Extracted abstracts                |
| `results/acknowledgements.json`         | Extracted acknowledgements         |
| `results/topics.csv`, `topic_words.csv` | Topic assignments and words        |
| `results/similarity_scores.csv`         | Pairwise similarity scores         |
| `results/similar_papers_edges.csv`      | Similar paper links                |
| `results/ner_entities.json`             | Extracted people and organizations |
| `results/grant_ids.csv`                 | Extracted grant/project IDs        |
| `results/funding_relations.csv`         | Funding relations                  |
| `results/external_enrichment.json`      | OpenAlex and Wikidata enrichment   |
| `results/knowledge_graph.ttl`           | Final RDF Knowledge Graph          |
| `figures/*.png`                         | Generated plots                    |

## Knowledge Graph

The Knowledge Graph is built in RDF/Turtle with `rdflib`. It represents papers, topics, people, organizations, grants, funders and similarity relations. It reuses standard vocabularies such as DCTerms, FOAF, PROV and schema.org.

## External enrichment

The graph is enriched with:

| Source         | Adds                                                                  |
| -------------- | --------------------------------------------------------------------- |
| OpenAlex       | Paper IDs, publication year, venue, citations, OA status and concepts |
| Wikidata / ROR | Organization IDs, country and official website                        |

These links are added with `owl:sameAs`, making the graph more interoperable.

## Reproducibility and open science

The project supports reproducibility through pinned dependencies, fixed random seeds, Docker/Compose, CI tests, no hardcoded paths, PROV-O provenance and RO-Crate packaging.

It also follows open science practices with an open-access corpus, MIT license, citation metadata, documentation, RDF Knowledge Graph and SPARQL queries.

## License and citation

The project is released under the **MIT License**. Citation information is provided in `CITATION.cff`.
