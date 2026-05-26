
# Model & Method Decisions

| Task                 | Model / Method              | Reason                                                              | Output                          | Validation                             |
| -------------------- | --------------------------- | ------------------------------------------------------------------- | ------------------------------- | -------------------------------------- |
| Abstract embeddings  | `all-MiniLM-L6-v2`          | Lightweight open HuggingFace model for semantic text representation | 384-d embeddings                | Nearest-pair inspection                |
| Topic modeling       | BERTopic + KMeans           | Produces topic words; KMeans works better for the small corpus      | `topics.csv`, `topic_words.csv` | Silhouette score + top-word inspection |
| Number of topics     | Silhouette over k = 2..8    | Objective way to choose the best k                                  | Best k                          | Silhouette plot                        |
| Paper similarity     | Cosine similarity           | Standard metric for comparing embeddings                            | `similarity_scores.csv`         | Distribution plot + top-pair review    |
| Similarity threshold | 0.65                        | Chosen from score distribution                                      | `similar_papers_edges.csv`      | Similarity distribution check          |
| NER                  | `roberta-large-ner-english` | Pre-trained HuggingFace model for people and organizations          | `ner_entities.json`             | Manual review                          |
| Grant IDs            | Regex patterns              | Better suited for grant/project identifiers than NER                | `grant_ids.csv`                 | Manual check                           |
| Funder association   | Cue-word heuristic          | Links grants to nearby funding organizations                        | `funding_relations.csv`         | Manual check                             |
| Knowledge Graph      | RDF/Turtle with `rdflib`    | FAIR, reusable and queryable with SPARQL                            | `knowledge_graph.ttl`           | RDF parse + SPARQL checks              |
| Provenance           | PROV-O                      | Standard provenance model                                           | `sample_run_prov.ttl`           | RDF parse                              |
| Research Object      | RO-Crate 1.1                | Packages research artifacts in a standard format                    | `ro-crate-metadata.json`        | Valid JSON-LD                          |

# Reproducibility of model choices

To make the model choices reproducible, all models are fixed by name in config/config.yaml, and library versions are listed in requirements.txt. Random seeds are fixed for KMeans and UMAP to reduce variation between runs. The same embedding model is used for both topic modeling and similarity analysis, ensuring that both tasks rely on the same semantic representation.

