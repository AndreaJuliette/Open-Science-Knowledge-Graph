
# External Enrichment Sources

The Knowledge Graph is enriched using two external open sources through `src/enrich_external_sources.py`. This enrichment is **additive**: it only adds external identifiers and metadata, without changing topic modeling, similarity or NER.

## Sources

| Source       | Type            | Enriches      | Main data added                                                           | Linking                          |
| ------------ | --------------- | ------------- | ------------------------------------------------------------------------- | -------------------------------- |
| **OpenAlex** | REST API / JSON | Papers        | OpenAlex ID, publication year, venue, citation count, OA status, concepts | `owl:sameAs` to OpenAlex         |
| **Wikidata** | SPARQL / RDF    | Organizations | Wikidata QID, ROR ID, country, official website                           | `owl:sameAs` to Wikidata and ROR |

## OpenAlex

OpenAlex enriches paper nodes using DOI lookup first, and title search if no DOI match is found. It was selected because it is open, requires no API key, has broad scholarly coverage, and provides useful bibliometric metadata not available in the PDFs.

## Wikidata

Wikidata enriches organization nodes using SPARQL label matching, restricted to organization entities to reduce false positives. It was selected because it is an open RDF/SPARQL Linked Open Data source and provides identifiers such as ROR, as well as country and website information.

## Outputs and reproducibility

The enrichment produces `results/external_enrichment.json` and `results/external_links.csv`. It can be run with:

```bash
python -m src.pipeline --steps enrich
```

Failures or missing matches are logged and skipped, so the workflow can continue. Main limitations are possible mismatches from title-based OpenAlex search or label-based Wikidata matching.
