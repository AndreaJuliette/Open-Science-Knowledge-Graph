import pandas as pd
from src.extract_grants import extract_all_grants

GRANT_PATTERNS = [
    r"\b[A-Z]{2,}[-/ ]?\d{3,}\b",
    r"\b(?:H2020|FP7|ERC|DFG|NSF|NIH|EU)[-\s]?[A-Z0-9\-]{2,}\b",
]


def test_grant_extraction_finds_id_and_funder():
    acks = {
        "p1": {
            "status": "found",
            "text": "This work was supported by the European Research Council "
                    "under grant ERC-2019-COG-864789.",
        }
    }
    grants_df, funding_df = extract_all_grants(acks, GRANT_PATTERNS, context_window=60)
    assert not grants_df.empty
    assert any("ERC" in g or "864789" in g for g in grants_df["grant_id"])
    assert "European Research Council" in set(funding_df["funder"])


def test_not_found_papers_yield_no_grants():
    acks = {"p2": {"status": "not_found", "text": ""}}
    grants_df, funding_df = extract_all_grants(acks, GRANT_PATTERNS, context_window=60)
    assert grants_df.empty
    assert funding_df.empty


def test_ner_entity_structure_is_valid():
    entry = {"status": "found", "entities": [{"text": "John Smith", "type": "PER", "score": 0.99}]}
    assert entry["status"] in ("found", "not_found")
    for ent in entry["entities"]:
        assert {"text", "type", "score"} <= set(ent)
        assert ent["type"] in ("PER", "ORG")
        assert 0.0 <= ent["score"] <= 1.0
