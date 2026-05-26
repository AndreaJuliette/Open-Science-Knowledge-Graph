
from __future__ import annotations

import logging
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)

WIKIDATA_ENTITY = "http://www.wikidata.org/entity/"

def _openalex_get(url: str, params: dict, timeout: int) -> dict | None:
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.warning("OpenAlex request failed (%s): %s", url, exc)
        return None


def _extract_openalex_fields(work: dict, max_concepts: int) -> dict:
    full_id = work.get("id", "")
    short_id = full_id.rsplit("/", 1)[-1] if full_id else None
    venue = None
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    venue = source.get("display_name") or (work.get("host_venue") or {}).get("display_name")
    concepts = [c.get("display_name") for c in (work.get("concepts") or [])[:max_concepts]
                if c.get("display_name")]
    return {
        "openalex_id": short_id,
        "openalex_url": full_id or None,
        "publication_year": work.get("publication_year"),
        "venue": venue,
        "cited_by_count": work.get("cited_by_count"),
        "open_access_status": (work.get("open_access") or {}).get("oa_status"),
        "concepts": concepts,
    }


def enrich_paper_openalex(doi: str, title: str, base_url: str, mailto: str, timeout: int, max_concepts: int) -> dict | None:
    """Search for a paper in OpenAlex using DOI first, then title."""

    params = {"mailto": mailto} if mailto else {}

    doi = (doi or "").strip()
    if doi and not doi.lower().startswith("10.xxxx"):
        work = _openalex_get(f"{base_url.rstrip('/')}/works/doi:{doi}", params, timeout)
        if work and work.get("id"):
            return _extract_openalex_fields(work, max_concepts)

    title = (title or "").strip()
    if title and not title.startswith("TODO"):
        data = _openalex_get(
            f"{base_url.rstrip('/')}/works",
            {**params, "search": title, "per_page": 1},
            timeout,
        )
        results = (data or {}).get("results") or []
        if results:
            return _extract_openalex_fields(results[0], max_concepts)

    return None



WIKIDATA_ORG_QUERY = """
SELECT ?item ?ror ?countryLabel ?website WHERE {{
  ?item rdfs:label "{label}"@en .
  ?item wdt:P31/wdt:P279* wd:Q43229 .          # instance of (subclass of) organization
  OPTIONAL {{ ?item wdt:P6782 ?ror. }}          # ROR ID
  OPTIONAL {{ ?item wdt:P17 ?country. }}         # country
  OPTIONAL {{ ?item wdt:P856 ?website. }}        # official website
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 1
"""


def enrich_org_wikidata(name: str, endpoint: str, timeout: int, user_agent: str) -> dict | None:
    """Look up an organization on Wikidata and return fields."""

    query = WIKIDATA_ORG_QUERY.format(label=name.replace('"', '\\"'))
    try:
        resp = requests.get(endpoint,params={"query": query, "format": "json"},headers={"User-Agent": user_agent, "Accept": "application/sparql-results+json"},timeout=timeout)
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Wikidata request failed for %r: %s", name, exc)
        return None

    if not bindings:
        return None
    
    b = bindings[0]
    item_uri = b.get("item", {}).get("value", "")
    qid = item_uri.rsplit("/", 1)[-1] if item_uri else None
    ror = b.get("ror", {}).get("value")
    return {
        "wikidata_id": qid,
        "wikidata_url": item_uri or None,
        "ror_id": (f"https://ror.org/{ror}" if ror else None),
        "country": b.get("countryLabel", {}).get("value"),
        "official_website": b.get("website", {}).get("value"),
    }


def collect_org_names(ner_entities: dict, funding_df: pd.DataFrame) -> list[str]:
    names: set[str] = set()
    for entry in (ner_entities or {}).values():
        for ent in entry.get("entities", []):
            if ent.get("type") == "ORG":
                names.add(ent["text"])
    if funding_df is not None and not funding_df.empty:
        for funder in funding_df["funder"]:
            if str(funder).strip() and str(funder) != "unknown":
                names.add(str(funder))
    return sorted(names)


def enrich_all(metadata_df: pd.DataFrame,ner_entities: dict,funding_df: pd.DataFrame,cfg: dict) -> tuple[dict, pd.DataFrame]:
    """Run both enrichments and return (enrichment_dict, links_df)."""
    
    enrichment: dict = {"papers": {}, "organizations": {}}
    links: list[dict] = []

    oa = cfg.get("openalex", {})
    wd = cfg.get("wikidata", {})

    if metadata_df is not None and not metadata_df.empty:
        for _, row in metadata_df.iterrows():
            pid = str(row.get("paper_id", "")).strip()
            if not pid or pid.startswith("TODO"):
                continue
            fields = enrich_paper_openalex(
                doi=str(row.get("doi", "")), title=str(row.get("title", "")),
                base_url=oa.get("base_url", "https://api.openalex.org"),
                mailto=oa.get("mailto", ""), timeout=oa.get("timeout", 30),
                max_concepts=oa.get("max_concepts", 5),
            )
            if fields and fields.get("openalex_id"):
                enrichment["papers"][pid] = fields
                links.append({
                    "local_type": "Paper", "local_id": pid, "source": "OpenAlex",
                    "link_type": "openAlexId", "external_id": fields["openalex_id"],
                    "external_url": fields["openalex_url"] or "",
                })
                logger.info("OpenAlex: %s -> %s", pid, fields["openalex_id"])

    if wd.get("enrich_organizations", True):
        delay = float(wd.get("request_delay", 1.0))
        ua = wd.get("user_agent", "Assignment2-KG/1.0")
        for name in collect_org_names(ner_entities, funding_df):
            fields = enrich_org_wikidata(
                name, endpoint=wd.get("endpoint", "https://query.wikidata.org/sparql"),
                timeout=wd.get("timeout", 30), user_agent=ua,
            )
            if fields and fields.get("wikidata_id"):
                enrichment["organizations"][name] = fields
                links.append({
                    "local_type": "Organization", "local_id": name, "source": "Wikidata",
                    "link_type": "wikidataId", "external_id": fields["wikidata_id"],
                    "external_url": fields["wikidata_url"] or "",
                })
                if fields.get("ror_id"):
                    links.append({
                        "local_type": "Organization", "local_id": name, "source": "ROR",
                        "link_type": "rorId", "external_id": fields["ror_id"],
                        "external_url": fields["ror_id"],
                    })
                logger.info("Wikidata: %r -> %s", name, fields["wikidata_id"])
            if delay:
                time.sleep(delay)

    links_df = pd.DataFrame(
        links, columns=["local_type", "local_id", "source", "link_type", "external_id", "external_url"]
    )
    logger.info(
        "External enrichment: %d papers (OpenAlex), %d organizations (Wikidata).",
        len(enrichment["papers"]), len(enrichment["organizations"]),
    )
    return enrichment, links_df
