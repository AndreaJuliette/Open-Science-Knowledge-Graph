import json
from pathlib import Path

import pandas as pd
from rdflib import Graph
from rdflib import RDF, Namespace
from rdflib.namespace import DCTERMS
from src.build_kg import build_graph, serialize_graph

ROOT = Path(__file__).resolve().parent.parent
ONT_IRI = "http://example.org/oskg/ontology#"
BASE_IRI = "http://example.org/oskg/resource/"


def sample_graph() -> Graph:
    metadata = pd.DataFrame([{
        "paper_id": "p1", "title": "A Paper on Graphs", "authors": "Jane Doe; Max Roe",
        "year": 2024, "doi": "10.1/x", "url": "https://example.com/p1", "source": "arXiv",
        "license": "CC-BY-4.0", "open_access": True, "access_date": "2026-05-24",
        "pdf_path": "data/papers/p1.pdf",
    }])
    abstracts = {"p1": "abstract about knowledge graphs", "p2": "abstract about embeddings"}
    topics = pd.DataFrame([
        {"paper_id": "p1", "topic": 0, "topic_label": "graphs, rdf", "top_words": "graphs, rdf"},
        {"paper_id": "p2", "topic": 0, "topic_label": "graphs, rdf", "top_words": "graphs, rdf"},
    ])
    edges = pd.DataFrame([{"source_paper": "p1", "target_paper": "p2", "similarity": 0.81}])
    ner = {"p1": {"status": "found",
                  "entities": [{"text": "European Research Council", "type": "ORG", "score": 0.97}]}}
    grants = pd.DataFrame([{"paper_id": "p1", "grant_id": "ERC-864789", "context": "..."}])
    funding = pd.DataFrame([{"paper_id": "p1", "funder": "European Research Council", "grant_id": "ERC-864789"}])
    return build_graph(metadata, abstracts, topics, edges, ner, grants, funding,
                       BASE_IRI, ONT_IRI, {"topic": "m", "similarity": "m", "ner": "m"})


def test_kg_builds_and_parse(tmp_path):
    g = sample_graph()
    assert len(g) > 0
    out = tmp_path / "kg.ttl"
    serialize_graph(g, out)
    reparsed = Graph().parse(str(out), format="turtle")
    assert len(reparsed) == len(g)


def test_kg_contains_expected_classes():
    ttl = sample_graph().serialize(format="turtle")
    for cls in ["oskg:Paper", "oskg:Topic", "oskg:Organization",
                "oskg:SimilarityRelation", "oskg:Project"]:
        assert cls in ttl, f"missing class in KG: {cls}"


def test_every_paper_has_identifier():
    g = sample_graph()
    OSKG = Namespace(ONT_IRI)
    papers = list(g.subjects(RDF.type, OSKG.Paper))
    assert papers
    for p in papers:
        assert (p, DCTERMS.identifier, None) in g


def test_external_enrichment_triples():
    enrichment = {
        "papers": {
            "p1": {
                "openalex_id": "W123", "openalex_url": "https://openalex.org/W123",
                "publication_year": 2024, "venue": "Journal of KG",
                "cited_by_count": 7, "open_access_status": "gold",
                "concepts": ["Knowledge graph", "Semantic web"],
            }
        },
        "organizations": {
            "European Research Council": {
                "wikidata_id": "Q1377030", "wikidata_url": "https://www.wikidata.org/entity/Q1377030",
                "ror_id": "https://ror.org/0472cxd90", "country": "Belgium",
                "official_website": "https://erc.europa.eu",
            }
        },
    }
    import pandas as pd
    meta = pd.DataFrame([{"paper_id": "p1", "title": "A Paper", "authors": "Jane Doe",
                          "year": 2024, "doi": "10.1/x", "url": "https://example.com/p1",
                          "source": "arXiv", "license": "CC-BY", "open_access": True,
                          "access_date": "2026-05-24", "pdf_path": "data/papers/p1.pdf"}])
    g = build_graph(meta, {"p1": "abstract"}, pd.DataFrame(), pd.DataFrame(), {},
                    pd.DataFrame(), pd.DataFrame(), BASE_IRI, ONT_IRI,
                    external_enrichment=enrichment)
    ttl = g.serialize(format="turtle")
    for token in ["oskg:openAlexId", "oskg:venue", "oskg:citedByCount",
                  "oskg:openAccessStatus", "oskg:wikidataId", "oskg:rorId",
                  "oskg:country", "owl:sameAs"]:
        assert token in ttl, f"missing enrichment token: {token}"


def test_ontology_parses():
    g = Graph().parse(str(ROOT / "ontology" / "ontology.ttl"), format="turtle")
    assert len(g) > 0


def test_prov_trace_parses():
    g = Graph().parse(str(ROOT / "provenance" / "sample_run_prov.ttl"), format="turtle")
    assert len(g) > 0


def test_rocrate_metadata_is_valid_jsonld():
    data = json.loads((ROOT / "ro-crate" / "ro-crate-metadata.json").read_text(encoding="utf-8"))
    assert "@context" in data
    assert "@graph" in data and isinstance(data["@graph"], list)
