import numpy as np

from src.compute_similarity import cosine_similarity_matrix, edges_df, similarity_long_df


def test_cosine_matrix_range_and_diagonal():
    rng = np.random.default_rng(0)
    emb = rng.normal(size=(5, 8))
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
    sim = cosine_similarity_matrix(emb)
    assert sim.shape == (5, 5)
    assert sim.max() <= 1.0 + 1e-9
    assert sim.min() >= -1.0 - 1e-9
    assert np.allclose(np.diag(sim), 1.0, atol=1e-6)


def test_long_df_shape_and_columns():
    ids = ["a", "b", "c"]
    sim = np.array([[1.0, 0.9, 0.1], [0.9, 1.0, 0.2], [0.1, 0.2, 1.0]])
    long = similarity_long_df(ids, sim)
    assert len(long) == 3 
    assert set(long.columns) == {"paper_a", "paper_b", "similarity"}
    assert (long["similarity"] <= 1.0).all()


def test_edges_threshold_filtering():
    ids = ["a", "b", "c"]
    sim = np.array([[1.0, 0.9, 0.1], [0.9, 1.0, 0.2], [0.1, 0.2, 1.0]])
    long = similarity_long_df(ids, sim)
    edges = edges_df(long, threshold=0.75)
    assert len(edges) == 1
    assert set(edges.columns) == {"source_paper", "target_paper", "similarity"}
    assert (edges["similarity"] >= 0.75).all()
