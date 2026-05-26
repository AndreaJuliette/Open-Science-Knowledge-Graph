from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import FOAF, PROV, RDF, RDFS, XSD

logger = logging.getLogger(__name__)

# (activity_local, label, [input entity keys], [output entity keys], [agent keys])
_STEPS = [
    ("pdf-parsing", "PDF parsing", ["corpus", "config"], ["tei"], ["pipeline", "grobid", "group"]),
    ("abstract-extraction", "Abstract extraction", ["tei", "config"], ["abstracts"], ["pipeline", "group"]),
    ("acknowledgement-extraction", "Acknowledgement extraction", ["tei", "config"], ["acknowledgements"], ["pipeline", "group"]),
    ("topic-modeling", "Topic modeling", ["abstracts", "config"], ["topics"], ["pipeline", "embedding_model", "group"]),
    ("similarity-computation", "Similarity computation", ["abstracts", "config"], ["similarity"], ["pipeline", "embedding_model", "group"]),
    ("ner-extraction", "NER extraction", ["acknowledgements", "config"], ["ner"], ["pipeline", "ner_model", "group"]),
    ("grant-extraction", "Grant extraction", ["acknowledgements", "config"], ["grants"], ["pipeline", "group"]),
    ("kg-construction", "KG construction", ["metadata", "abstracts", "topics", "similarity", "ner", "grants"], ["kg"], ["pipeline", "group"]),
    ("ro-crate-generation", "RO-Crate generation", ["kg", "metadata"], ["rocrate"], ["pipeline", "group"]),
]

_ENTITIES = {
    "corpus": ("data/papers/", "Corpus of open-access PDF papers"),
    "config": ("config/config.yaml", "Pipeline configuration"),
    "metadata": ("data/papers_metadata.csv", "Corpus metadata"),
    "tei": ("results/tei/", "Grobid TEI-XML files"),
    "abstracts": ("results/abstracts.json", "Extracted abstracts"),
    "acknowledgements": ("results/acknowledgements.json", "Extracted acknowledgements"),
    "topics": ("results/topics.csv", "Topic assignments"),
    "similarity": ("results/similarity_scores.csv", "Pairwise similarity scores"),
    "ner": ("results/ner_entities.json", "NER entities"),
    "grants": ("results/grant_ids.csv", "Extracted grant IDs"),
    "kg": ("results/knowledge_graph.ttl", "RDF Knowledge Graph"),
    "rocrate": ("ro-crate/ro-crate-metadata.json", "RO-Crate metadata"),
}


def generate_prov(cfg: dict, run_timestamp: str | None = None) -> Graph:
    """Build the PROV-O graph for a sample run."""
    base = cfg["project"]["base_iri"]
    RES = Namespace(base)
    PLAN = Namespace(base + "plan/")
    g = Graph()
    g.bind("prov", PROV)
    g.bind("foaf", FOAF)
    g.bind("res", RES)

    ts = run_timestamp or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    agents = {
        "group": (RES["agent/group7"], PROV.Person, cfg["project"]["group"]),
        "pipeline": (RES["agent/pipeline"], PROV.SoftwareAgent, "Assignment 2 Python pipeline (src/pipeline.py)"),
        "grobid": (RES["agent/grobid"], PROV.SoftwareAgent, "Grobid 0.8.1 TEI extraction service"),
        "embedding_model": (RES["agent/embedding-model"], PROV.SoftwareAgent, cfg["similarity"]["embedding_model"]),
        "ner_model": (RES["agent/ner-model"], PROV.SoftwareAgent, cfg["ner"]["model"]),
    }
    for uri, atype, label in agents.values():
        g.add((uri, RDF.type, PROV.Agent))
        g.add((uri, RDF.type, atype))
        g.add((uri, RDFS.label, Literal(label)))
    g.add((agents["group"][0], FOAF.name, Literal(cfg["project"]["group"])))


    ent_uri: dict[str, URIRef] = {}
    for key, (path, desc) in _ENTITIES.items():
        uri = RES[f"entity/{key}"]
        ent_uri[key] = uri
        g.add((uri, RDF.type, PROV.Entity))
        g.add((uri, RDFS.label, Literal(desc)))
        g.add((uri, PROV.atLocation, Literal(path)))


    for local, label, inputs, outputs, agent_keys in _STEPS:
        act = RES[f"activity/{local}"]
        plan = PLAN[local]
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, RDFS.label, Literal(label)))
        g.add((act, PROV.startedAtTime, Literal(ts, datatype=XSD.dateTime)))
        g.add((plan, RDF.type, PROV.Plan))
        for k in inputs:
            if k in ent_uri:
                g.add((act, PROV.used, ent_uri[k]))
        for k in outputs:
            if k in ent_uri:
                g.add((ent_uri[k], PROV.wasGeneratedBy, act))
                for ik in inputs:
                    if ik in ent_uri:
                        g.add((ent_uri[k], PROV.wasDerivedFrom, ent_uri[ik]))
        for ak in agent_keys:
            assoc_agent = agents.get(ak)
            if assoc_agent:
                g.add((act, PROV.wasAssociatedWith, assoc_agent[0]))

        assoc = RES[f"activity/{local}/association"]
        g.add((act, PROV.qualifiedAssociation, assoc))
        g.add((assoc, RDF.type, PROV.Association))
        g.add((assoc, PROV.agent, agents["pipeline"][0]))
        g.add((assoc, PROV.hadPlan, plan))

    logger.info("PROV trace built: %d triples.", len(g))
    return g


def write_prov(cfg: dict, prov_dir: Path, run_timestamp: str | None = None) -> Path:
    """Write sample_run_prov.ttl"""
    prov_dir.mkdir(parents=True, exist_ok=True)
    g = generate_prov(cfg, run_timestamp)
    ttl_path = prov_dir / "sample_run_prov.ttl"
    g.serialize(destination=str(ttl_path), format="turtle")

    logger.info("PROV files written to %s", prov_dir)
    return ttl_path
