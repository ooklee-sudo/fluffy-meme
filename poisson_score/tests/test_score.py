import numpy as np
from poisson_score import score_text, tokenize, extract_events
from poisson_score.score import score_counts


def _doc(rng, positions_fn, n=4000):
    toks = ["word"] * n
    for i in positions_fn(n, rng):
        toks[i] = "("
    return " ".join(toks)


def test_events_basic():
    t = tokenize("Furthermore, the results were obtained (see [1]); in contrast, adoption is increasing.")
    ev = extract_events(t)
    assert len(ev["P"]) == 5 and len(ev["D"]) == 2 and len(ev["N"]) >= 2


def test_poisson_counts_score_low_and_regular_or_clumped_high():
    rng = np.random.default_rng(1)
    pois = score_counts(rng.poisson(2.0, 100))
    regular = score_counts(np.full(100, 2))
    clumped = score_counts(np.where(rng.random(100) < .5, 0, 4))
    assert pois.hellinger < 0.15 and regular.hellinger > 0.4 and clumped.hellinger > 0.4
    assert regular.dispersion < 0.1 and clumped.dispersion > 1.5


def test_text_level_regular_vs_random():
    rng = np.random.default_rng(2)
    rand = _doc(rng, lambda n, r: r.choice(n, 40, replace=False))
    reg = _doc(rng, lambda n, r: range(10, n, 100))
    assert score_text(reg).score > score_text(rand).score


def test_short_doc_nan():
    assert np.isnan(score_text("too short").score)
