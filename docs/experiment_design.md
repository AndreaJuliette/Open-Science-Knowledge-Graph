
## Experiment Design

### Objective

Perform advanced analysis on a corpus of **30 open-access research papers** by identifying topics, measuring semantic similarity, extracting acknowledged people, organizations and grant/project identifiers, and representing the results as a **FAIR RDF Knowledge Graph** queryable with SPARQL. The workflow is reproducible, documented, provenance-tracked and packaged as a Research Object. 

### Research Questions

* **RQ1:** What are the main topics in the corpus?
* **RQ2:** Which papers are semantically similar based on their abstracts?
* **RQ3:** Which persons, organizations and grants are mentioned in acknowledgements?
* **RQ4:** How can topics, similarity relations, metadata and funding information be represented as a FAIR Knowledge Graph?

### Inputs

| Input                      | Description                               |
| -------------------------- | ----------------------------------------- |
| `data/papers/*.pdf`        | The 30 research papers.                   |
| `data/papers_metadata.csv` | Bibliographic and license metadata.       |
| `config/config.yaml`       | Parameters, models, thresholds and paths. |

### Pipeline

`parse → abstracts → acknowledgements → topics → similarity → ner → grants → external_enrichment → kg → prov → rocrate`

Each step writes outputs to `results/`, making the workflow independently re-runnable.

### Methods

* **Topic modeling:** BERTopic with KMeans over `all-MiniLM-L6-v2` abstract embeddings; `k` selected using silhouette score.
* **Similarity:** cosine similarity between abstract embeddings; pairs above the threshold become `similar_to` edges.
* **NER and grants:** pre-trained HuggingFace NER model for persons and organizations; regex for grant/project identifiers. No fine-tuning is performed.
* **External enrichment:** OpenAlex and Wikidata/SemOpenAlex add external identifiers and bibliometric metadata without changing the core analysis.

### Knowledge Graph

The RDF/Turtle Knowledge Graph is built with `rdflib`. It includes papers, people, organizations, projects, topics and similarity relations, reusing vocabularies such as DCTerms, FOAF, PROV-O and schema.org.

### Outputs

Main outputs include abstracts, acknowledgements, topic results, similarity scores, extracted entities, grant IDs, funding relations, the RDF Knowledge Graph, figures, provenance files and the RO-Crate package.

### Validation and Reproducibility

Topics are validated through silhouette scores and top-word inspection; similarity through distribution checks and review of top pairs; and the Knowledge Graph through RDF parsing, SPARQL checks and coverage counts. Reproducibility is supported through pinned dependencies, Docker/Compose, fixed random seeds, deterministic configuration and CI.

### Limitations

The study is exploratory due to the small corpus size. Other limitations include abstract-only similarity, variable acknowledgement coverage, possible NER errors and regex false positives.
