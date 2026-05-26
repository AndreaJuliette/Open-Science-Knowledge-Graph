Claro, aquí tienes una versión más resumida:

# Corpus — 30 Open-Access Research Papers

This directory documents the corpus used by the Assignment 2 pipeline.

> **Status: template.** The 30 PDFs are not included yet. They must be added to `data/papers/`, and `papers_metadata.csv` must be completed with one row per paper. Current rows are `TODO_xxxx` placeholders.

## Origin and selection

The corpus must contain **30 open-access papers**. Their source and selection criteria should be documented, for example: database or venue, topic, year range, language, availability of PDF, and presence of abstracts.

The corpus size is fixed by the assignment. Since 30 papers is small, the analyses are exploratory.

## Licensing and access

Only open-access papers are used. Each paper’s license is recorded in `papers_metadata.csv`.

PDFs are not committed to Git by default because redistribution rights may vary. Metadata and derived results are tracked instead.

All papers were retrieved on **2026-05-24**. Update the access date when the corpus is finalized.

## Metadata columns

| Column        | Description                                 |
| ------------- | ------------------------------------------- |
| `paper_id`    | Stable ID; must match the PDF filename stem |
| `title`       | Paper title                                 |
| `authors`     | Authors separated by `;`                    |
| `year`        | Publication year                            |
| `doi`         | DOI             |
| `url`         | Landing page or PDF URL                     |
| `source`      | Source such as arXiv, OpenAlex or journal   |
| `license`     | License                       |
| `open_access` | -----------------                           |
| `access_date` | Retrieval date                              |
| `pdf_path`    | Path to the PDF                             |

## How to add the corpus

1. Add the 30 PDFs to `data/papers/`.
2. Name each PDF with a clean ID, for example `2603.09896v1.pdf`.
3. Add one row per paper to `papers_metadata.csv`.
4. Make sure `paper_id` matches the PDF filename stem.
5. Run the pipeline.

