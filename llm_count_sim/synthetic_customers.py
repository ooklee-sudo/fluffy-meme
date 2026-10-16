"""Ground-truth customer generator and LLM-synthetic customer conditions A-D.

IMPORTANT: `MockLLM` is an assumption-driven stand-in that encodes failure modes reported in the
silicon-sampling literature (mode collapse, rounding to "nice" numbers, shrinkage toward the
group mean, Poisson-like independent daily decisions). It is NOT a measurement of any real LLM.
Replace it with `llm_client.AnthropicLLM` to run the same pipeline on a real model.
"""
from dataclasses import dataclass

import numpy as np

SEGMENTS = {  # name: (share, base weekly-rate multiplier)
    "light": (0.50, 0.35), "regular": (0.35, 1.0), "heavy": (0.15, 2.6)}


@dataclass
class Population:
    segment: np.ndarray   # segment index per customer
    treat: np.ndarray     # 0/1 promo exposure
    lam: np.ndarray       # true individual rate (only the generator knows this)
    y: np.ndarray         # real counts


def make_real(n, rng, base=2.0, shape=1.2, zero_infl=0.10, true_irr=1.25, window_weeks=4):
    """Gamma-Poisson (NB) heterogeneity + structural zeros + promo effect."""
    shares = np.array([s for s, _ in SEGMENTS.values()])
    mult = np.array([m for _, m in SEGMENTS.values()])
    seg = rng.choice(len(shares), n, p=shares)
    treat = rng.integers(0, 2, n)
    gamma = rng.gamma(shape, 1 / shape, n)                 # individual heterogeneity, mean 1
    lam = base * window_weeks / 4 * mult[seg] * gamma * np.where(treat == 1, true_irr, 1.0)
    inactive = rng.random(n) < zero_infl
    y = np.where(inactive, 0, rng.poisson(lam))
    return Population(seg, treat, lam, y)


class MockLLM:
    """Stand-in for an LLM that only 'knows' persona-level information (segment, promo)."""

    def __init__(self, rng, base=2.0, window_weeks=4, promo_overreact=1.0):
        self.rng, self.base, self.w = rng, base, window_weeks
        self.mult = np.array([m for _, m in SEGMENTS.values()])
        self.promo = 1.25 ** promo_overreact  # >1 exponent => exaggerated promo response

    def _persona_mean(self, pop):
        return self.base * self.w / 4 * self.mult[pop.segment] * np.where(pop.treat == 1, self.promo, 1.0)

    def direct_answer(self, pop):  # condition A: "how many purchases in 4 weeks?"
        mu = self._persona_mean(pop) * self.rng.lognormal(0, 0.15, len(pop.segment))
        nice = np.array([0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20])      # round-number anchoring
        return nice[np.abs(mu[:, None] - nice[None]).argmin(1)]

    def daily_decisions(self, pop, days=28):  # condition B: independent Bernoulli per day
        p = np.clip(self._persona_mean(pop) / days, 0, 1)
        return self.rng.binomial(days, p)

    def described_dispersion(self):  # condition C: model "describes" a too-tame dispersion
        return 8.0  # NB shape k (var = mu + mu^2/k); true k~1.2, LLM says near-Poisson

    def context_multiplier(self, pop):  # condition D: LLM adds only persona-level context
        return self._persona_mean(pop) / (self.base * self.w / 4)


def cond_A(pop, llm, rng):
    return llm.direct_answer(pop)


def cond_B(pop, llm, rng):
    return llm.daily_decisions(pop)


def cond_C(pop, llm, rng):
    mu, k = llm._persona_mean(pop), llm.described_dispersion()
    return rng.poisson(rng.gamma(k, mu / k))


def cond_D(pop, llm, rng, pilot=None):
    """Hybrid: externally injected Gamma heterogeneity. Shape k is estimated by method of moments
    from a small real pilot (y, segment), using WITHIN-segment moments so that between-segment
    variance (already carried by the LLM's persona means) is not double counted."""
    k = 1.5
    if pilot is not None:
        py, pseg = pilot
        num = den = 0.0
        for g in np.unique(pseg):
            yg = py[pseg == g]
            if len(yg) > 5 and yg.mean() > 0:
                m, v = yg.mean(), yg.var(ddof=1)
                num += len(yg) * m ** 2
                den += len(yg) * max(v - m, 1e-6)
        k = float(np.clip(num / den, 0.3, 50)) if den > 0 else 50.0
    mu = llm._persona_mean(pop)
    return rng.poisson(rng.gamma(k, mu / k))


CONDITIONS = {"A direct": cond_A, "B daily-sim": cond_B, "C describe→sample": cond_C, "D hybrid": cond_D}
