# Sample run — provenance summary

- Group: Group 7
- Pipeline version: 1.0.0
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- NER model: Jean-Baptiste/roberta-large-ner-english

## Activities
- **PDF parsing**: used `corpus, config` → generated `tei`
- **Abstract extraction**: used `tei, config` → generated `abstracts`
- **Acknowledgement extraction**: used `tei, config` → generated `acknowledgements`
- **Topic modeling**: used `abstracts, config` → generated `topics`
- **Similarity computation**: used `abstracts, config` → generated `similarity`
- **NER extraction**: used `acknowledgements, config` → generated `ner`
- **Grant extraction**: used `acknowledgements, config` → generated `grants`
- **KG construction**: used `metadata, abstracts, topics, similarity, ner, grants` → generated `kg`
