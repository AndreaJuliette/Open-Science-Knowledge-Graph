
from __future__ import annotations

import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def embed_texts(texts: list[str], model_name: str) -> np.ndarray:
    """Return L2-normalized embeddings (n_texts x dim) for each text."""

    logger.info("Loading embedding model: %s", model_name)
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,  
        show_progress_bar=False,
    )
    return embeddings


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between all embeddings."""

    similarity_matrix = embeddings @ embeddings.T
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    return similarity_matrix


def similarity_long_df(paper_ids: list[str], sim: np.ndarray) -> pd.DataFrame:
    """Create a table with one row per pair of papers."""

    rows = []
    n = len(paper_ids)
    for i in range(n):
        for j in range(i + 1, n):
            rows.append(
                {
                    "paper_a": paper_ids[i],
                    "paper_b": paper_ids[j],
                    "similarity": round(float(sim[i, j]), 6),
                }
            )

    similarity_df = pd.DataFrame(rows)
    similarity_df = similarity_df.sort_values("similarity", ascending=False, ignore_index=True)

    return similarity_df


def edges_df(long_df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Filter pairwise similarities to edges with similarity >= threshold. """

    kept = long_df[long_df["similarity"] >= threshold].copy()
    kept = kept.rename(columns={"paper_a": "source_paper", "paper_b": "target_paper"})
    kept = kept.reset_index(drop=True)
    logger.info("Similarity edges: %d/%d pairs >= threshold %.2f",len(kept), len(long_df), threshold)
    return kept[["source_paper", "target_paper", "similarity"]]


def plot_similarity_distribution(long_df: pd.DataFrame,threshold: float,output_path: Path,) -> Path:
    """Save a histogram of pairwise similarities."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(long_df["similarity"],bins=20)

    ax.axvline(threshold,linestyle="--",label=f"threshold = {threshold}")

    ax.set_xlabel("Cosine similarity")
    ax.set_ylabel("Number of paper pairs")
    ax.set_title("Distribution of pairwise abstract similarity")
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Similarity distribution saved to %s", output_path)

    return output_path


def compute_similarity(abstracts: dict[str, str],model_name: str,) -> tuple[list[str], np.ndarray]:
    """Embed abstracts and return paper IDs with their similarity matrix."""

    paper_ids = sorted(abstracts)

    texts = []
    for paper_id in paper_ids:
        texts.append(abstracts[paper_id])

    embeddings = embed_texts(texts, model_name)

    similarity_matrix = cosine_similarity_matrix(embeddings)

    return paper_ids, similarity_matrix
