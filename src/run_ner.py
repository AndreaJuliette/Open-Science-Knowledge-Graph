
from __future__ import annotations
from transformers import pipeline

import logging

logger = logging.getLogger(__name__)

NOT_FOUND = "not_found"


def load_ner_pipeline(model_name: str,aggregation_strategy: str = "simple",):
    """Load a HuggingFace NER model."""

    logger.info("Loading NER model: %s", model_name)

    return pipeline(
        task="token-classification",
        model=model_name,
        aggregation_strategy=aggregation_strategy,
    )


def normalize_entity(text: str) -> str:
    """Clean an entity name."""

    return " ".join(text.split()).strip(" .,;:")


def extract_entities(text: str,ner_pipeline,min_score: float,keep_types: list[str]) -> list[dict]:
    """Extract entities from one acknowledgement text."""

    if not text.strip():
        return []

    raw_entities = ner_pipeline(text)

    entities_by_key: dict[tuple[str, str], dict] = {}

    for entity in raw_entities:
        entity_type = entity.get("entity_group") or entity.get("entity")

        if entity_type not in keep_types:
            continue

        score = float(entity.get("score", 0.0))

        if score < min_score:
            continue

        entity_text = normalize_entity(entity.get("word", ""))

        if len(entity_text) < 2:
            continue

        key = (entity_text.lower(), entity_type)

        current_entity = {
            "text": entity_text,
            "type": entity_type,
            "score": round(score, 4),
        }

        if key not in entities_by_key:
            entities_by_key[key] = current_entity
        elif score > entities_by_key[key]["score"]:
            entities_by_key[key] = current_entity

    return sorted(
        entities_by_key.values(),
        key=lambda entity: (-entity["score"], entity["text"]),
    )


def run_ner(acknowledgements: dict[str, dict[str, str]],model_name: str,aggregation_strategy: str,min_score: float,keep_types: list[str]) -> dict[str, dict]:
    """Extract entities from all acknowledgement texts."""

    ner_pipeline = load_ner_pipeline(model_name=model_name,aggregation_strategy=aggregation_strategy)

    results: dict[str, dict] = {}

    for paper_id, acknowledgement in sorted(acknowledgements.items()):
        status = acknowledgement.get("status")
        text = acknowledgement.get("text", "")

        if status != "found" or not text:
            results[paper_id] = {
                "status": NOT_FOUND,
                "entities": [],
            }
            continue

        entities = extract_entities(text=text,ner_pipeline=ner_pipeline,min_score=min_score,keep_types=keep_types)

        results[paper_id] = {
            "status": "found",
            "entities": entities,
        }

        logger.info("%s: %d entities", paper_id, len(entities))

    return results
