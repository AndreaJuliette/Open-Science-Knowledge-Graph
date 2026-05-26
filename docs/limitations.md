
# Limitations

The main limitations of this project are related to the corpus size, extraction quality, model performance and external enrichment.

## Main limitations

* The corpus contains only **30 papers**, so the results are exploratory and cannot be generalized.
* Topics and similarity are based only on **abstracts**, not full texts.
* PDF parsing with Grobid may miss or incorrectly extract some sections.
* Some papers do not include acknowledgements, so no entities can be extracted from them.
* The pre-trained NER model may misclassify people and organizations, miss acronyms, or split long names incorrectly.
* Grant extraction relies on regex patterns, which can produce false positives or miss unusual formats.
* Funder detection is heuristic, so some funders may remain unknown.
* Entity linking is based on surface forms, which can leave duplicates or ambiguous entities.
* External enrichment from OpenAlex and Wikidata is best-effort and may fail due to missing data, matching errors, or lack of internet access.
* OpenAlex and Wikidata data can change over time, so enriched metadata represents a snapshot.
* Minor nondeterminism may remain despite fixed seeds.

## Future work

Future improvements include full-text analysis, a larger corpus, better entity linking with ORCID/ROR/Wikidata, a domain-specific NER model, and a Zenodo DOI for publication.
