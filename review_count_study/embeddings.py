"""Text-embedding features for the RQ2 comparison (M4/M5): low-dimensional dense text representation.

Backends
  tfidf : TF-IDF -> truncated SVD (LSA). Offline, deterministic, no downloads. Default.
  st    : sentence-transformers model (pip install sentence-transformers; downloads weights on first use),
          then PCA. Typically a stronger representation than LSA.
Reduction (SVD/PCA) is unsupervised and fit on all analysis texts, so no outcome information leaks into the
features; document this as transductive. Columns are named emb_0..emb_{k-1}.
"""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer


def embed_texts(texts, backend="tfidf", dim=20, st_model="sentence-transformers/all-MiniLM-L6-v2", seed=0):
    texts = pd.Series(texts).fillna("").tolist()
    if backend == "tfidf":
        X = TfidfVectorizer(min_df=2, sublinear_tf=True, ngram_range=(1, 2), max_features=50_000).fit_transform(texts)
        k = min(dim, X.shape[1] - 1)
        Z = TruncatedSVD(k, random_state=seed).fit_transform(X)
    elif backend == "st":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError("pip install sentence-transformers for --embedding st") from e
        E = SentenceTransformer(st_model).encode(texts, batch_size=64, show_progress_bar=False)
        Z = PCA(min(dim, E.shape[1]), random_state=seed).fit_transform(E)
    else:
        raise ValueError(backend)
    Z = (Z - Z.mean(0)) / np.where(Z.std(0) == 0, 1, Z.std(0))  # standardize for comparable IRRs (per 1 SD)
    return pd.DataFrame(Z, columns=[f"emb_{i}" for i in range(Z.shape[1])])


def add_embeddings(df, backend="tfidf", dim=20, **kw):
    """Returns (df with emb_* columns, list of emb column names). Index-aligned."""
    emb = embed_texts(df["text"], backend, dim, **kw)
    emb.index = df.index
    return pd.concat([df, emb], axis=1), list(emb.columns)
