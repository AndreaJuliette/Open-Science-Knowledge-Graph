from __future__ import annotations

import logging
from pathlib import Path
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from src.compute_similarity import embed_texts
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


def select_k_by_silhouette(embeddings: np.ndarray,k_min: int,k_max: int,random_state: int,) -> tuple[int, pd.DataFrame]:
    """Choose the number of clusters with the best silhouette score."""

    n_docs = embeddings.shape[0]
    min_k = max(2, k_min)
    max_k = min(k_max, n_docs - 1)

    results = []

    for k in range(min_k, max_k + 1):
        kmeans = KMeans(
            n_clusters=k,
            random_state=random_state,
            n_init=10,
        )

        labels = kmeans.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)

        results.append({
            "k": k,
            "silhouette_score": round(float(score), 6),
        })

        logger.info("k=%d -> silhouette=%.4f", k, score)

    scores_df = pd.DataFrame(results)

    best_row = scores_df["silhouette_score"].idxmax()
    best_k = int(scores_df.loc[best_row, "k"])

    logger.info("Selected k=%d by silhouette.", best_k)
    return best_k, scores_df


def run_topic_modeling(abstracts: dict[str, str],embedding_model: str,k_min: int,k_max: int,top_n_words: int,random_state: int,umap_n_neighbors: int,umap_n_components: int,min_df: int,ngram_range: tuple[int, int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    """Run BERTopic+KMeans and return (topics_df, topic_words_df, silhouette_df).

    - topics_df: paper_id, topic, topic_label, top_words
    - topic_words_df: topic, rank, word, weight
    - silhouette_df: k, silhouette_score
    """

    paper_ids = sorted(abstracts)
    docs = [abstracts[pid] for pid in paper_ids]

    embeddings = embed_texts(docs, embedding_model)
    best_k, silhouette_df = select_k_by_silhouette(embeddings, k_min, k_max, random_state)

    n_docs = len(docs)

    umap_model = UMAP(
        n_neighbors=min(umap_n_neighbors, max(2, n_docs - 1)),
        n_components=min(umap_n_components, max(2, n_docs - 2)),
        min_dist=0.0,
        metric="cosine",
        random_state=random_state,
    )

    cluster_model = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    vectorizer_model = CountVectorizer(
        stop_words="english", min_df=min_df, ngram_range=tuple(ngram_range)
    )

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=cluster_model,  
        vectorizer_model=vectorizer_model,
        top_n_words=top_n_words,
        calculate_probabilities=False,
        verbose=False,
    )
    topics, _ = topic_model.fit_transform(docs, embeddings=embeddings)

    word_rows = []
    labels: dict[int, str] = {}
    for topic_id in sorted(set(topics)):
        words = topic_model.get_topic(topic_id) or []
        labels[topic_id] = ", ".join(w for w, _ in words[:5]) or f"topic_{topic_id}"
        for rank, (word, weight) in enumerate(words, start=1):
            word_rows.append(
                {"topic": topic_id, "rank": rank, "word": word, "weight": round(float(weight), 6)}
            )
    topic_words_df = pd.DataFrame(word_rows)

    topics_df = pd.DataFrame(
        {
            "paper_id": paper_ids,
            "topic": topics,
            "topic_label": [labels[t] for t in topics],
        }
    )
    topics_df["top_words"] = topics_df["topic"].map(labels)
    logger.info("Topic modeling produced %d topics over %d papers.", len(set(topics)), n_docs)
    return topics_df, topic_words_df, silhouette_df


def plot_silhouette(silhouette_df: pd.DataFrame, output_path: Path) -> Path:
    """Save a plot of silhouette score vs number of clusters."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    best_index = silhouette_df["silhouette_score"].idxmax()
    best_row = silhouette_df.loc[best_index]
    best_k = int(best_row["k"])

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(silhouette_df["k"],silhouette_df["silhouette_score"],marker="o")

    ax.axvline(best_k,linestyle="--",label=f"best k = {best_k}",)

    ax.set_xlabel("k (number of clusters)")
    ax.set_ylabel("Silhouette score")
    ax.set_title("Silhouette score vs number of topics")
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Silhouette plot saved to %s", output_path)

    return output_path


def plot_topic_distribution(topics_df: pd.DataFrame,output_path: Path,) -> Path:
    """Save a bar chart with the number of papers per topic."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    topic_counts = topics_df["topic"].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.bar(
        topic_counts.index.astype(str),
        topic_counts.values,
    )

    ax.set_xlabel("Topic")
    ax.set_ylabel("Number of papers")
    ax.set_title("Papers per topic")

    # Save plot
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    logger.info("Topic distribution plot saved to %s", output_path)

    return output_path
