
from __future__ import annotations

import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def parse_pdf(pdf_path: Path, grobid_url: str, timeout: int = 120) -> str:

    """Send one PDF to Grobid and return the TEI-XML as a string."""

    endpoint = f"{grobid_url.rstrip('/')}/api/processFulltextDocument"
    with open(pdf_path, "rb") as pdf:
        response = requests.post(
            endpoint,
            files={"input": pdf},
            data={
                "consolidateHeader": "1",
                "includeRawAffiliations": "1",
            },
            timeout=timeout,
        )
    response.raise_for_status()
    return response.text


def parse_all_pdfs(
    input_dir: Path,
    tei_dir: Path,
    grobid_url: str,
    timeout: int = 120,
) -> list[Path]:
    """Parse every .pdf in input_dir into TEI-XML files."""

    tei_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning("No PDF files found in %s", input_dir)
        return []

    xml_paths: list[Path] = []
    for pdf_path in pdf_files:

        logger.info("Parsing %s ...", pdf_path.name)

        try:
            tei_xml = parse_pdf(pdf_path, grobid_url, timeout)
        except requests.RequestException as exc:
            logger.error("Failed to parse %s: %s", pdf_path.name, exc)
            continue

        xml_out = tei_dir / pdf_path.with_suffix(".xml").name
        xml_out.write_text(tei_xml, encoding="utf-8")
        xml_paths.append(xml_out)
        logger.info(" XML created -> %s", xml_out.name)

    logger.info("Parsed %d/%d PDFs.", len(xml_paths), len(pdf_files))
    return xml_paths
