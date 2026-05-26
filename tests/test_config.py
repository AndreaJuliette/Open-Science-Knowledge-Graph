from pathlib import Path

import pandas as pd

from src.pipeline import load_config

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "config.yaml"


def test_config_loads_and_has_sections():
    cfg = load_config(CONFIG)
    for section in ["project", "grobid", "paths", "topic_modeling", "similarity", "ner", "grants", "kg"]:
        assert section in cfg, f"missing config section: {section}"
    assert cfg["project"]["base_iri"].startswith("http")
    assert cfg["project"]["ontology_iri"].startswith("http")


def test_required_path_keys():
    cfg = load_config(CONFIG)
    for key in ["input_dir", "metadata_csv", "tei_dir", "results_dir", "figures_dir"]:
        assert key in cfg["paths"], f"missing paths.{key}"


def test_thresholds_and_k_are_sane():
    cfg = load_config(CONFIG)
    assert 0.0 <= cfg["similarity"]["threshold"] <= 1.0
    assert cfg["topic_modeling"]["k_min"] >= 2
    assert cfg["topic_modeling"]["k_max"] >= cfg["topic_modeling"]["k_min"]


def test_metadata_csv_has_required_columns():
    df = pd.read_csv(ROOT / "data" / "papers_metadata.csv")
    required = {
        "paper_id", "title", "authors", "year", "doi", "url",
        "source", "license", "open_access", "access_date", "pdf_path",
    }
    assert required.issubset(set(df.columns)), f"missing columns: {required - set(df.columns)}"
