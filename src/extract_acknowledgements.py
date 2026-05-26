
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)

TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}

NOT_FOUND = "not_found"


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def extract_acknowledgement(xml_path: Path) -> dict[str, str]:
    """Return {"status": ..., "text": ...}  for one TEI-XML file."""

    tree = etree.parse(str(xml_path))
    fragments: list[str] = []

    for div in tree.iter(f"{{{TEI_NS}}}div"):
        div_type = (div.get("type") or "").lower()
        if "acknowledg" in div_type or "funding" in div_type:
            txt = _clean(" ".join(div.itertext()))
            if txt:
                fragments.append(txt)

    for note in tree.iter(f"{{{TEI_NS}}}note"):
        note_type = (note.get("type") or "").lower()
        if "funding" in note_type or "acknowledg" in note_type:
            txt = _clean(" ".join(note.itertext()))
            if txt:
                fragments.append(txt)

    seen: set[str] = set()
    unique: list[str] = []

    for fragment in fragments:
        if fragment not in seen:
            unique.append(fragment)
            seen.add(fragment)

    text = _clean(" ".join(unique))

    if text:
        return {"status": "found", "text": text}
    return {"status": NOT_FOUND, "text": ""}


def extract_all_acknowledgements(tei_dir: Path) -> dict[str, dict[str, str]]:
    """Extract acknowledgements for every TEI-XML file in tei_dir."""

    results: dict[str, dict[str, str]] = {}
    found = 0
    for xml_path in sorted(tei_dir.glob("*.xml")):
        entry = extract_acknowledgement(xml_path)
        results[xml_path.stem] = entry
        if entry["status"] == "found":
            found += 1
            logger.info("Acknowledgement found: %s", xml_path.stem)
        else:
            logger.info("Acknowledgement not found: %s", xml_path.stem)
    logger.info("Acknowledgements found in %d/%d papers.", found, len(results))
    return results
