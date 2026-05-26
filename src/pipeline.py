"""End-to-end pipeline orchestrator for Assignment 2.

Runs (or replays) the steps that turn 30 PDFs into an RDF Knowledge Graph:

    parse -> abstracts -> acknowledgements -> topics -> similarity
          -> ner -> grants -> evaluate -> kg -> prov -> rocrate

Design notes
------------
* All paths come from ``config/config.yaml`` — nothing is hardcoded.
* Steps hand off through files in ``results/`` (like Assignment 1), so any step
  can be re-run in isolation with ``--steps``; inputs are loaded from disk if not
  in memory.
* Heavy/optional model steps (topics, similarity, ner) degrade gracefully: a
  missing optional dependency is logged clearly and skipped, never a hard crash.

Usage
-----
    python -m src.pipeline --config config/config.yaml
    python -m src.pipeline --steps kg,prov,rocrate
    python -m src.pipeline --skip parse
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.parse_pdfs import parse_all_pdfs
from src.extract_abstracts import extract_all_abstracts
from src.extract_acknowledgements import extract_all_acknowledgements
from src.topic_modeling import (plot_silhouette, plot_topic_distribution, run_topic_modeling)
from src.compute_similarity import (compute_similarity, edges_df, plot_similarity_distribution, similarity_long_df)
from src.enrich_external_sources import enrich_all
from src.build_kg import build_graph, serialize_graph

logger = logging.getLogger("pipeline")

STEP_ORDER = [
    "parse", "abstracts", "acknowledgements", "topics", "similarity",
    "ner", "grants", "enrich", "kg", "prov",
]


def load_config(config_path: Path) -> dict:
    """Load the YAML configuration file."""
    with open(config_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _resolve_paths(cfg: dict, root: Path) -> dict[str, Path]:
    p = cfg["paths"]
    results = root / p["results_dir"]
    figures = root / p["figures_dir"]
    return {
        "root": root,
        "input_dir": root / p["input_dir"],
        "metadata_csv": root / p["metadata_csv"],
        "gold_standard_ner": root / p["gold_standard_ner"],
        "tei_dir": root / p["tei_dir"],
        "results": results,
        "figures": figures,
        "abstracts": results / "abstracts.json",
        "acknowledgements": results / "acknowledgements.json",
        "topics": results / "topics.csv",
        "topic_words": results / "topic_words.csv",
        "silhouette": results / "silhouette_scores.csv",
        "similarity": results / "similarity_scores.csv",
        "edges": results / "similar_papers_edges.csv",
        "ner": results / "ner_entities.json",
        "grants": results / "grant_ids.csv",
        "funding": results / "funding_relations.csv",
        "enrichment": results / "external_enrichment.json",
        "external_links": results / "external_links.csv",
        "kg": results / cfg["kg"]["output"],
        "provenance_dir": root / "provenance",
        "ro_crate_dir": root / "ro-crate",
    }


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s", path)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Wrote %s (%d rows)", path, len(df))


def _setup_logging(cfg: dict, results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, cfg.get("logging", {}).get("level", "INFO"))
    log_file = results_dir / cfg.get("logging", {}).get("file", "pipeline.log")
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")],
    )


def run(config_path: Path, project_root: Path, steps: list[str]) -> None:
    """Execute the requested pipeline steps in canonical order."""

    cfg = load_config(config_path)
    paths = _resolve_paths(cfg, project_root)
    _setup_logging(cfg, paths["results"])
    paths["figures"].mkdir(parents=True, exist_ok=True)

    logger.info("Running steps: %s", ", ".join(steps))
    ctx: dict = {}  

    if "parse" in steps:
        
        grobid_url = os.environ.get("GROBID_URL", cfg["grobid"]["server_url"])
        logger.info("STEP parse: Grobid at %s", grobid_url)
        parse_all_pdfs(paths["input_dir"], paths["tei_dir"], grobid_url, cfg["grobid"]["timeout"])


    if "abstracts" in steps:
        
        ctx["abstracts"] = extract_all_abstracts(paths["tei_dir"])
        _write_json(ctx["abstracts"], paths["abstracts"])


    if "acknowledgements" in steps:
       
        ctx["acknowledgements"] = extract_all_acknowledgements(paths["tei_dir"])
        _write_json(ctx["acknowledgements"], paths["acknowledgements"])

    if "topics" in steps:
        abstracts = _get_abstracts(ctx, paths)
        if not abstracts:
            logger.warning("STEP topics: no abstracts available — skipping.")
        else:
            try:
    
                tcfg = cfg["topic_modeling"]
                topics_df, topic_words_df, silhouette_df = run_topic_modeling(
                    abstracts,
                    embedding_model=tcfg["embedding_model"],
                    k_min=tcfg["k_min"], k_max=tcfg["k_max"],
                    top_n_words=tcfg["top_n_words"], random_state=tcfg["random_state"],
                    umap_n_neighbors=tcfg["umap_n_neighbors"],
                    umap_n_components=tcfg["umap_n_components"],
                    min_df=tcfg["min_df"], ngram_range=tcfg["ngram_range"],
                )
                _write_csv(topics_df, paths["topics"])
                _write_csv(topic_words_df, paths["topic_words"])
                _write_csv(silhouette_df, paths["silhouette"])
                plot_silhouette(silhouette_df, paths["figures"] / "silhouette_scores.png")
                plot_topic_distribution(topics_df, paths["figures"] / "topic_distribution.png")
            except ImportError as exc:
                logger.error("STEP topics skipped (missing optional dependency): %s", exc)


    if "similarity" in steps:
        abstracts = _get_abstracts(ctx, paths)
        if not abstracts:
            logger.warning("STEP similarity: no abstracts available — skipping.")
        else:
            try:
                
                scfg = cfg["similarity"]
                ids, sim = compute_similarity(abstracts, scfg["embedding_model"])
                long_df = similarity_long_df(ids, sim)
                edges = edges_df(long_df, scfg["threshold"])
                _write_csv(long_df, paths["similarity"])
                _write_csv(edges, paths["edges"])
                plot_similarity_distribution(
                    long_df, scfg["threshold"], paths["figures"] / "similarity_distribution.png"
                )
            except ImportError as exc:
                logger.error("STEP similarity skipped (missing optional dependency): %s", exc)

    if "ner" in steps:
        acks = _get_acknowledgements(ctx, paths)
        if acks is None:
            logger.warning("STEP ner: no acknowledgements available — skipping.")
        else:
            try:
                from src.run_ner import run_ner

                ncfg = cfg["ner"]
                ctx["ner"] = run_ner(
                    acks, model_name=ncfg["model"],
                    aggregation_strategy=ncfg["aggregation_strategy"],
                    min_score=ncfg["min_score"], keep_types=ncfg["keep_types"],
                )
                _write_json(ctx["ner"], paths["ner"])
            except ImportError as exc:
                logger.error("STEP ner skipped (missing optional dependency): %s", exc)

    # 7. Grants
    if "grants" in steps:
        acks = _get_acknowledgements(ctx, paths)
        if acks is None:
            logger.warning("STEP grants: no acknowledgements available — skipping.")
        else:
            from src.extract_grants import extract_all_grants

            gcfg = cfg["grants"]
            grant_ids_df, funding_df = extract_all_grants(
                acks, gcfg["patterns"], gcfg["context_window"]
            )
            _write_csv(grant_ids_df, paths["grants"])
            _write_csv(funding_df, paths["funding"])

    if "enrich" in steps:
        ecfg = cfg.get("external_enrichment", {})
        if not ecfg.get("enabled", False):
            logger.info("STEP enrich: disabled in config — skipping.")
        else:
            try:
                
                ctx["enrichment"], links_df = enrich_all(
                    metadata_df=_read_csv(paths["metadata_csv"]),
                    ner_entities=ctx.get("ner") or _read_json(paths["ner"]) or {},
                    funding_df=_read_csv(paths["funding"]),
                    cfg=ecfg,
                )
                _write_json(ctx["enrichment"], paths["enrichment"])
                _write_csv(links_df, paths["external_links"])
            except ImportError as exc:
                logger.error("STEP enrich skipped (missing optional dependency): %s", exc)


    if "kg" in steps:

        graph = build_graph(
            metadata_df=_read_csv(paths["metadata_csv"]),
            abstracts=_get_abstracts(ctx, paths),
            topics_df=_read_csv(paths["topics"]),
            edges_df=_read_csv(paths["edges"]),
            ner_entities=ctx.get("ner") or _read_json(paths["ner"]) or {},
            grant_ids_df=_read_csv(paths["grants"]),
            funding_df=_read_csv(paths["funding"]),
            base_iri=cfg["project"]["base_iri"],
            ontology_iri=cfg["project"]["ontology_iri"],
            models={
                "topic": cfg["topic_modeling"]["embedding_model"],
                "similarity": cfg["similarity"]["embedding_model"],
                "ner": cfg["ner"]["model"],
            },
            external_enrichment=ctx.get("enrichment") or _read_json(paths["enrichment"]) or {},
        )
        serialize_graph(graph, paths["kg"])

    if "prov" in steps:
        from src.generate_prov import write_prov

        write_prov(cfg, paths["provenance_dir"])

    logger.info("Pipeline finished. Outputs in %s", paths["results"])



def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _get_abstracts(ctx: dict, paths: dict) -> dict[str, str]:
    if "abstracts" not in ctx:
        ctx["abstracts"] = _read_json(paths["abstracts"]) or {}
    return ctx["abstracts"]


def _get_acknowledgements(ctx: dict, paths: dict):
    if "acknowledgements" not in ctx:
        ctx["acknowledgements"] = _read_json(paths["acknowledgements"])
    return ctx["acknowledgements"]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assignment 2 KG pipeline.")
    parser.add_argument("--config", type=Path, default=Path("config/config.yaml"))
    parser.add_argument(
        "--steps", default="all",
        help="Comma-separated subset of: " + ",".join(STEP_ORDER) + " (default: all)",
    )
    parser.add_argument("--skip", default="", help="Comma-separated steps to skip.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    selected = STEP_ORDER if args.steps == "all" else [s.strip() for s in args.steps.split(",")]
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    steps = [s for s in STEP_ORDER if s in selected and s not in skip]

    project_root = Path(__file__).resolve().parent.parent
    run(args.config, project_root, steps)


if __name__ == "__main__":
    main()
