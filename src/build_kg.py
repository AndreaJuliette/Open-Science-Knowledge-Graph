
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, OWL, PROV, RDF, RDFS, SKOS, XSD

logger = logging.getLogger(__name__)

SCHEMA = Namespace("https://schema.org/")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(text).strip().lower()).strip("-")
    return s or "unknown"


def build_graph(
    metadata_df: pd.DataFrame,
    abstracts: dict[str, str],
    topics_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    ner_entities: dict[str, dict],
    grant_ids_df: pd.DataFrame,
    funding_df: pd.DataFrame,
    base_iri: str,
    ontology_iri: str,
    models: dict[str, str] | None = None,
    external_enrichment: dict | None = None,
) -> Graph:
    """Return a RDF graph."""
    models = models or {}
    OSKG = Namespace(ontology_iri)
    RES = Namespace(base_iri)
    g = Graph()
    g.bind("oskg", OSKG)
    g.bind("res", RES)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("prov", PROV)
    g.bind("skos", SKOS)
    g.bind("schema", SCHEMA)
    g.bind("owl", OWL)

    def paper_uri(pid: str) -> URIRef:
        return RES[f"paper/{_slug(pid)}"]

    
    kg_node = RES["knowledge-graph"]
    build_activity = RES["activity/kg-construction"]
    g.add((kg_node, RDF.type, PROV.Entity))
    g.add((kg_node, RDF.type, SCHEMA.Dataset))
    g.add((kg_node, PROV.wasGeneratedBy, build_activity))
    g.add((build_activity, RDF.type, PROV.Activity))
    for label, model in models.items():
        g.add((build_activity, OSKG.usedModel, Literal(f"{label}: {model}")))

    meta_by_id: dict[str, dict] = {}
    if not metadata_df.empty:
        for _, row in metadata_df.iterrows():
            meta_by_id[str(row["paper_id"])] = row.to_dict()

    known_ids = set(abstracts) | set(meta_by_id)
    if not topics_df.empty:
        known_ids |= set(topics_df["paper_id"].astype(str))
    for pid in sorted(known_ids):
        p = paper_uri(pid)
        g.add((p, RDF.type, OSKG.Paper))
        g.add((p, DCTERMS.identifier, Literal(pid)))

        meta = meta_by_id.get(pid, {})
        title = str(meta.get("title", "")).strip()
        if title and not title.startswith("TODO"):
            g.add((p, DCTERMS.title, Literal(title)))
        doi = str(meta.get("doi", "")).strip()
        if doi and not doi.startswith("10.xxxx"):
            g.add((p, OSKG.hasDOI, Literal(doi)))
        url = str(meta.get("url", "")).strip()
        if url and "example.org" not in url and "xxxx" not in url:
            g.add((p, OSKG.hasURL, URIRef(url)))
        year = str(meta.get("year", "")).strip()
        if year.isdigit():
            g.add((p, OSKG.publicationYear, Literal(int(year), datatype=XSD.gYear)))
        if pid in abstracts:
            g.add((p, DCTERMS.abstract, Literal(abstracts[pid])))

        authors = str(meta.get("authors", "")).strip()
        if authors and not authors.startswith("TODO"):
            for author in [a.strip() for a in authors.split(";") if a.strip()]:
                a_uri = RES[f"person/{_slug(author)}"]
                g.add((a_uri, RDF.type, OSKG.Person))
                g.add((a_uri, FOAF.name, Literal(author)))
                g.add((p, OSKG.hasAuthor, a_uri))

    if not topics_df.empty:
        for topic_id, grp in topics_df.groupby("topic"):
            t_uri = RES[f"topic/{topic_id}"]
            label = str(grp["topic_label"].iloc[0])
            g.add((t_uri, RDF.type, OSKG.Topic))
            g.add((t_uri, RDFS.label, Literal(label)))
            g.add((t_uri, SKOS.prefLabel, Literal(label)))
            if "topic" in models:
                g.add((t_uri, OSKG.usedModel, Literal(models["topic"])))
            for pid in grp["paper_id"]:
                g.add((paper_uri(pid), OSKG.belongs_to_topic, t_uri))

 
    if not edges_df.empty:
        for _, row in edges_df.iterrows():
            a, b = paper_uri(row["source_paper"]), paper_uri(row["target_paper"])
            g.add((a, OSKG.similar_to, b))
            g.add((b, OSKG.similar_to, a))  # symmetric
            rel = RES[f"similarity/{_slug(row['source_paper'])}__{_slug(row['target_paper'])}"]
            g.add((rel, RDF.type, OSKG.SimilarityRelation))
            g.add((rel, OSKG.sourcePaper, a))
            g.add((rel, OSKG.targetPaper, b))
            g.add((rel, OSKG.similarityScore, Literal(float(row["similarity"]), datatype=XSD.decimal)))
            if "similarity" in models:
                g.add((rel, OSKG.usedModel, Literal(models["similarity"])))

    for pid, entry in sorted(ner_entities.items()):
        for ent in entry.get("entities", []):
            etype = ent["type"]
            name = ent["text"]
            if etype == "PER":
                e_uri = RES[f"person/{_slug(name)}"]
                cls = OSKG.Person
            elif etype == "ORG":
                e_uri = RES[f"org/{_slug(name)}"]
                cls = OSKG.Organization
            else:
                continue
            g.add((e_uri, RDF.type, cls))
            g.add((e_uri, FOAF.name, Literal(name)))
            if "ner" in models:
                g.add((e_uri, OSKG.usedModel, Literal(models["ner"])))
            g.add((paper_uri(pid), OSKG.acknowledges, e_uri))

    if not grant_ids_df.empty:
        for _, row in grant_ids_df.iterrows():
            proj = RES[f"project/{_slug(row['grant_id'])}"]
            g.add((proj, RDF.type, OSKG.Project))
            g.add((proj, DCTERMS.identifier, Literal(str(row["grant_id"]))))
            g.add((proj, RDFS.label, Literal(str(row["grant_id"]))))
            g.add((paper_uri(row["paper_id"]), OSKG.mentionsGrant, proj))

    if not funding_df.empty:
        for _, row in funding_df.iterrows():
            funder = str(row["funder"]).strip()
            if funder and funder != "unknown":
                org = RES[f"org/{_slug(funder)}"]
                g.add((org, RDF.type, OSKG.Organization))
                g.add((org, FOAF.name, Literal(funder)))
                g.add((paper_uri(row["paper_id"]), OSKG.fundedBy, org))
                proj = RES[f"project/{_slug(row['grant_id'])}"]
                g.add((proj, OSKG.fundedBy, org))

    enrichment = external_enrichment or {}
    for pid, ext in (enrichment.get("papers") or {}).items():
        p = paper_uri(pid)
        g.add((p, RDF.type, OSKG.Paper))
        oa_id = ext.get("openalex_id")
        if oa_id:
            g.add((p, OSKG.openAlexId, Literal(oa_id)))
            g.add((p, OWL.sameAs, URIRef(ext.get("openalex_url") or f"https://openalex.org/{oa_id}")))
        if ext.get("publication_year"):
            g.add((p, OSKG.publicationYear, Literal(int(ext["publication_year"]), datatype=XSD.gYear)))
        if ext.get("venue"):
            g.add((p, OSKG.venue, Literal(str(ext["venue"]))))
        if ext.get("cited_by_count") is not None:
            g.add((p, OSKG.citedByCount, Literal(int(ext["cited_by_count"]), datatype=XSD.integer)))
        if ext.get("open_access_status"):
            g.add((p, OSKG.openAccessStatus, Literal(str(ext["open_access_status"]))))
        for concept in ext.get("concepts") or []:
            g.add((p, OSKG.openAlexConcept, Literal(str(concept))))

    for org_name, ext in (enrichment.get("organizations") or {}).items():
        org = RES[f"org/{_slug(org_name)}"]
        g.add((org, RDF.type, OSKG.Organization))
        g.add((org, FOAF.name, Literal(org_name)))
        if ext.get("wikidata_id"):
            g.add((org, OSKG.wikidataId, Literal(ext["wikidata_id"])))
            g.add((org, OWL.sameAs, URIRef(ext.get("wikidata_url") or f"https://www.wikidata.org/entity/{ext['wikidata_id']}")))
        if ext.get("ror_id"):
            g.add((org, OSKG.rorId, Literal(ext["ror_id"])))
            if str(ext["ror_id"]).startswith("http"):
                g.add((org, OWL.sameAs, URIRef(ext["ror_id"])))
        if ext.get("country"):
            g.add((org, OSKG.country, Literal(str(ext["country"]))))
        if ext.get("official_website"):
            g.add((org, OSKG.officialWebsite, URIRef(str(ext["official_website"]))))

    logger.info("Knowledge graph built: %d triples.", len(g))
    return g


def serialize_graph(g: Graph, output_path: Path) -> Path:

    """Serialize the graph to Turtle."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_path), format="turtle")
    logger.info("Knowledge graph written to %s", output_path)
    return output_path
