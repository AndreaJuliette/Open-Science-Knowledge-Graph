import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

UNKNOWN_FUNDER = "unknown"

FUNDER_PATTERN = re.compile(
    r"([A-Z][\w&.\-]+(?:\s+[A-Z][\w&.\-]+){0,6}\s+"
    r"(?:Foundation|Council|Agency|Ministry|Fund|Funds|Programme|Program|"
    r"Union|Society|Institute|Commission|Organization|Organisation|Office|"
    r"Department|Centre|Center|Association|Trust|Academy))"
)


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    compiled_patterns = []

    for pattern in patterns:
        compiled_patterns.append(re.compile(pattern))

    return compiled_patterns


def guess_funder(context: str) -> str:
    match = FUNDER_PATTERN.search(context)

    if match:
        return match.group(1).strip()

    return UNKNOWN_FUNDER


def get_context(text: str, start_index: int, end_index: int, window: int) -> str:
    context_start = max(0, start_index - window)
    context_end = min(len(text), end_index + window)

    context = text[context_start:context_end]
    context = " ".join(context.split())

    return context


def get_grant_id(match: re.Match) -> str:
    if match.groups():
        grant_id = match.group(1)
    else:
        grant_id = match.group(0)

    return grant_id.strip(" .,;:")


def extract_grants_from_text(text: str,patterns: list[re.Pattern],context_window: int,) -> list[dict]:
    """Extract grant IDs from one acknowledgement text."""

    if not text.strip():
        return []

    seen_grants: set[str] = set()
    grants: list[dict] = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            grant_id = get_grant_id(match)

            if len(grant_id) < 4:
                continue

            if grant_id in seen_grants:
                continue

            seen_grants.add(grant_id)

            context = get_context(text=text,start_index=match.start(),end_index=match.end(),window=context_window)

            grants.append(
                {
                    "grant_id": grant_id,
                    "context": context,
                    "funder": guess_funder(context),
                }
            )

    return grants


def extract_all_grants(acknowledgements: dict[str, dict[str, str]],patterns: list[str],context_window: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract grant IDs and funding relations from all papers."""

    compiled_patterns = compile_patterns(patterns)

    grant_rows: list[dict] = []
    funding_rows: list[dict] = []

    for paper_id, acknowledgement in sorted(acknowledgements.items()):
        if acknowledgement.get("status") != "found":
            continue

        text = acknowledgement.get("text", "")

        grants = extract_grants_from_text(text=text,patterns=compiled_patterns,context_window=context_window)

        for grant in grants:
            grant_rows.append(
                {
                    "paper_id": paper_id,
                    "grant_id": grant["grant_id"],
                    "context": grant["context"],
                }
            )

            funding_rows.append(
                {
                    "paper_id": paper_id,
                    "funder": grant["funder"],
                    "grant_id": grant["grant_id"],
                }
            )

    grant_ids_df = pd.DataFrame(grant_rows,columns=["paper_id", "grant_id", "context"],)

    funding_relations_df = pd.DataFrame(funding_rows,columns=["paper_id", "funder", "grant_id"])

    n_papers_with_grants = 0
    if not grant_ids_df.empty:
        n_papers_with_grants = grant_ids_df["paper_id"].nunique()

    logger.info("Extracted %d grant IDs across %d papers.",len(grant_ids_df),n_papers_with_grants,)

    return grant_ids_df, funding_relations_df
