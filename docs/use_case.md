# Use Case — What the Knowledge Graph is for

The Knowledge Graph is designed as a **research landscape explorer** for a curated corpus of 30 open-access papers. Instead of checking each PDF manually, users can query one graph to understand the main topics, related papers, acknowledged people and organizations, grants, funders, and external links to OpenAlex, Wikidata and ROR.

## What the graph connects

* **Papers ↔ topics:** what the corpus is about.
* **Papers ↔ papers:** which papers are semantically similar.
* **Papers ↔ people / organizations:** who is acknowledged.
* **Papers ↔ projects / funders:** who funded the work.
* **Papers / organizations ↔ external sources:** OpenAlex, Wikidata and ROR identifiers.

## Users and goals

| User                           | Goal                        | Example question                                               |
| ------------------------------ | --------------------------- | -------------------------------------------------------------- |
| Researcher           | Understand a field quickly  | What topics exist, and which papers are similar to paper X?    |
| Research          | Analyze funding             | Which funders and grants appear in the corpus?                 |
| Researcher | Assess impact and openness  | What are the citation counts and OA status of papers by topic? |
| Researcher                   | Connect with other datasets | Which organizations have Wikidata or ROR IDs?                  |

## Questions answered by the KG

| Question                              | SPARQL query                                   |
| ------------------------------------- | ---------------------------------------------- |
| What is the corpus about?             | `queries/papers_by_topic.rq`                   |
| Which papers are related?             | `queries/similar_papers.rq`                    |
| Who funds this research?              | `queries/funding_information.rq`               |
| Who is acknowledged?                  | `queries/papers_with_acknowledged_entities.rq` |
| Which organizations are most central? | `queries/papers_by_organization.rq`            |
| How impactful/open is the corpus?     | `queries/kg_summary.rq`                        |
