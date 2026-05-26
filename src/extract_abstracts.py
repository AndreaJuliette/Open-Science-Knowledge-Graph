
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)

TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}

def extract_abstract(xml_path: Path) -> str | None:
    """Return the abstract text from a TEI-XML file, or None if does not exist."""

    tree = etree.parse(str(xml_path))
    abstract_el = tree.find(".//tei:profileDesc/tei:abstract", namespaces=NSMAP)
    if abstract_el is None:
        logger.warning("No abstract element in %s", xml_path.name)
        return None
    text = " ".join(abstract_el.itertext()).split()
    text = " ".join(text).strip()
    return text or None


def extract_all_abstracts(tei_dir: Path) -> dict[str, str]:
    """Extract abstracts from every TEI-XML file in tei_dir."""

    abstracts: dict[str, str] = {}
    for xml_path in sorted(tei_dir.glob("*.xml")):
        abstract = extract_abstract(xml_path)
        if abstract:
            abstracts[xml_path.stem] = abstract
            logger.info("Abstract extracted: %s ", xml_path.stem)
        else:
            logger.warning("Abstract missing: %s", xml_path.stem)
    logger.info("Extracted %d abstracts.", len(abstracts))
    return abstracts
