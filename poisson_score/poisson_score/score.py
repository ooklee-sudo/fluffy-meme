"""Poisson-Score: distance of window-count distributions from a constant-rate
count process, per event family, averaged over families."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from .events import extract_events, tokenize

FAMILIES = ("P", "D", "N")
N_BINS = 5  # counts 0,1,2,3,4+


def window_counts(positions: list[int], n_tokens: int, L: int) -> np.ndarray:
    W = n_tokens // L
    if W == 0:
        return np.zeros(0, dtype=int)
    pos = np.asarray(positions, dtype=int)
    pos = pos[pos < W * L]
    return np.bincount(pos // L, minlength=W)


def _binned(counts: np.ndarray) -> np.ndarray:
    b = np.bincount(np.minimum(counts, N_BINS - 1), minlength=N_BINS).astype(float)
    return b / b.sum()


def poisson_pmf_binned(lam: float) -> np.ndarray:
    pm = stats.poisson.pmf(np.arange(N_BINS - 1), lam)
    return np.append(pm, max(0.0, 1.0 - pm.sum()))


def nb_pmf_binned(mean: float, var: float) -> np.ndarray:
    if var <= mean:  # no over-dispersion: fall back to Poisson
        return poisson_pmf_binned(mean)
    r = mean ** 2 / (var - mean)
    p = r / (r + mean)
    pm = stats.nbinom.pmf(np.arange(N_BINS - 1), r, p)
    return np.append(pm, max(0.0, 1.0 - pm.sum()))


def hellinger(p: np.ndarray, q: np.ndarray) -> float:
    bc = float(np.sum(np.sqrt(p * q)))
    return float(np.sqrt(max(0.0, 1.0 - bc)))


@dataclass
class FamilyResult:
    rate: float            # mean events per window
    dispersion: float      # index of dispersion s^2 / mean (nan if rate == 0)
    hellinger: float       # distance to Poisson(rate)
    p_disp: float          # two-sided chi-square dispersion-test p-value
    n_events: int


@dataclass
class DocResult:
    n_tokens: int
    n_windows: int
    score: float
    families: dict[str, FamilyResult] = field(default_factory=dict)
    nb_score: float = float("nan")


def score_counts(counts: np.ndarray) -> FamilyResult:
    W = len(counts)
    lam = float(counts.mean())
    if lam == 0:
        return FamilyResult(0.0, float("nan"), 0.0, float("nan"), 0)
    var = float(counts.var(ddof=1))
    disp = var / lam
    stat = (W - 1) * disp
    cdf = stats.chi2.cdf(stat, W - 1)
    p = float(2 * min(cdf, 1 - cdf))
    h = hellinger(_binned(counts), poisson_pmf_binned(lam))
    return FamilyResult(lam, disp, h, min(p, 1.0), int(counts.sum()))


def score_text(text: str, L: int = 200, min_windows: int = 5,
               reference: "NBReference | None" = None) -> DocResult:
    tokens = tokenize(text)
    ev = extract_events(tokens)
    W = len(tokens) // L
    if W < min_windows:
        return DocResult(len(tokens), W, float("nan"))
    fams = {}
    cmat = {}
    for k in FAMILIES:
        c = window_counts(ev[k], len(tokens), L)
        cmat[k] = c
        fams[k] = score_counts(c)
    res = DocResult(len(tokens), W, float(np.mean([f.hellinger for f in fams.values()])), fams)
    if reference is not None:
        res.nb_score = reference.score(cmat)
    return res


class NBReference:
    """Negative-binomial benchmark fitted on human documents (the NB-Score).

    Fits mean and variance of window counts per family on pooled human
    windows, so the benchmark allows for burstiness."""

    def __init__(self) -> None:
        self.params: dict[str, tuple[float, float]] = {}

    def fit(self, texts: list[str], L: int = 200) -> "NBReference":
        pools: dict[str, list[np.ndarray]] = {k: [] for k in FAMILIES}
        for t in texts:
            toks = tokenize(t)
            ev = extract_events(toks)
            for k in FAMILIES:
                c = window_counts(ev[k], len(toks), L)
                if len(c):
                    pools[k].append(c)
        for k in FAMILIES:
            allc = np.concatenate(pools[k])
            self.params[k] = (float(allc.mean()), float(allc.var(ddof=1)))
        return self

    def score(self, counts: dict[str, np.ndarray]) -> float:
        hs = [hellinger(_binned(counts[k]), nb_pmf_binned(*self.params[k])) for k in FAMILIES]
        return float(np.mean(hs))
