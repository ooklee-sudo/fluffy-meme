"""Pilot: do LLM synthetic customers reproduce real purchase-count distributions?

Conditions (Section 3.1 of the proposal):
  A direct   - ask for the 4-week purchase count
  B daily    - ask for a 28-day 0/1 purchase sequence, then sum
  C describe - ask for P(0..5+) and sample with an external RNG
  D hybrid   - LLM gives a contextual mean; external gamma injects heterogeneity

Usage:
  python run_pilot.py --mock --n 200                     # no key needed
  set OPENROUTER_API_KEY=...                             # Windows cmd
  python run_pilot.py --n 50 --model openai/gpt-4o-mini  # small trial first
"""
import argparse, json, os, re, sys, time, urllib.request
import numpy as np
import pandas as pd
from scipy import stats

# Retail II reference (proposal Section 4): mean 0.49, zero 0.73, alpha 3.05
REF_MEAN, REF_ALPHA = 0.49, 3.05
CONDS = ["A", "B", "C", "D"]
SEGMENTS = {  # segment -> relative mean multiplier (between-segment variance)
    "occasional gift buyer": 0.5, "regular small retailer": 1.6,
    "seasonal hobbyist": 0.8, "one-time bargain hunter": 0.3,
}


def make_personas(n, rng):
    segs = rng.choice(list(SEGMENTS), size=n)
    return pd.DataFrame({
        "id": range(n), "segment": segs,
        "age": rng.integers(22, 70, n),
        "country": rng.choice(["UK", "Germany", "France", "EIRE"], n, p=[.85, .05, .05, .05]),
    })


ANCHOR = (" Context: customers of this retailer make on average about 0.5 purchases "
          "per 4 weeks, and most make none.")


def persona_text(p, anchor=False):
    return (f"You are a customer of an online giftware retailer. Profile: {p.segment}, "
            f"age {p.age}, based in {p.country}. You made your first purchase 4 weeks ago."
            + (ANCHOR if anchor else ""))


def reference(n, rng):
    r = 1 / REF_ALPHA
    return rng.negative_binomial(r, r / (r + REF_MEAN), size=n)


# ---------------------------------------------------------------- LLM access
def call_llm(model, prompt, temperature, provider=None, retries=3):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set (or use --mock).")
    key = key.strip().strip('"')
    if not key.isascii() or " " in key:
        sys.exit("OPENROUTER_API_KEY looks invalid (non-ASCII or contains spaces). "
                 "Set it to your real key, e.g. sk-or-v1-...")
    body = {"model": model, "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]}
    if provider:
        body["provider"] = {"order": [provider], "allow_fallbacks": False}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["choices"][0]["message"]["content"]
        except Exception as e:
            if i == retries - 1:
                print(f"  call failed: {e}", file=sys.stderr)
                return ""
            time.sleep(2 ** (i + 1))


class MockLLM:
    """Implements assumed failure patterns (round numbers, narrow variance). NOT a real LLM."""
    def __init__(self, rng): self.rng = rng

    def __call__(self, prompt, seg_mult):
        m = REF_MEAN * seg_mult
        if "ONLY an integer" in prompt:
            return str(int(np.clip(round(m + self.rng.normal(0, 0.8)), 0, 6)))
        if "28" in prompt and "0/1" in prompt:
            return ",".join(str(int(x)) for x in (self.rng.random(28) < m / 28))
        if "probabilities" in prompt:
            p = np.exp(-np.arange(6) / max(m * 1.2, 0.3)); p /= p.sum()
            return json.dumps(dict(zip(["0", "1", "2", "3", "4", "5+"], p.round(3).tolist())))
        return f"{m:.3f}"


# ---------------------------------------------------------------- conditions
def prompts(p, anchor=False):
    base = persona_text(p, anchor)
    return {
        "A": base + " How many separate purchases will you make in the next 4 weeks? Answer with ONLY an integer.",
        "B": base + " For each of the next 28 days decide whether you make a purchase. Reply with ONLY 28 comma-separated 0/1 values.",
        "C": base + " Give the probabilities of making 0,1,2,3,4,5+ purchases in the next 4 weeks. Reply with ONLY JSON like {\"0\":..,\"1\":..,\"2\":..,\"3\":..,\"4\":..,\"5+\":..} summing to 1.",
        "D": base + " What is your expected average number of purchases per 4 weeks (can be fractional, e.g. 0.4)? Reply with ONLY a number.",
    }


def parse(cond, text, rng, alpha):
    try:
        if cond == "A":
            return max(0, int(re.search(r"\d+", text).group()))
        if cond == "B":
            v = [int(x) for x in re.findall(r"[01]", text)][:28]
            return sum(v) if len(v) == 28 else None
        if cond == "C":
            d = json.loads(re.search(r"\{.*\}", text, re.S).group())
            pr = np.array([float(d[k]) for k in ["0", "1", "2", "3", "4", "5+"]])
            return int(rng.choice([0, 1, 2, 3, 4, 5], p=pr / pr.sum()))
        if cond == "D":
            lam = max(float(re.search(r"\d*\.?\d+", text).group()), 1e-3)
            g = rng.gamma(1 / alpha, alpha)  # mean 1, variance alpha
            return int(rng.poisson(lam * g))
    except Exception:
        return None


# ---------------------------------------------------------------- metrics
def summarize(x):
    x = np.asarray(x, float); m, v = x.mean(), x.var(ddof=1)
    aux = ((x - m) ** 2 - x) / m if m > 0 else np.zeros_like(x)
    t = stats.ttest_1samp(aux, 0) if aux.std() > 0 else None
    return dict(n=len(x), mean=m, var_mean=v / m if m > 0 else np.nan, zero=(x == 0).mean(),
                alpha=(v - m) / m**2 if m > 0 else np.nan,
                poisson_reject=bool(t is not None and t.pvalue < .05 and t.statistic > 0))


def zero_at_mean(m):
    """P(0) of the reference NB (alpha=REF_ALPHA) rescaled to mean m: separates mean error from shape error."""
    return (1 + REF_ALPHA * m) ** (-1 / REF_ALPHA)


def distances(x, ref):
    k = int(max(x.max(), ref.max())) + 1
    px = np.bincount(x.astype(int), minlength=k) / len(x)
    pr = np.bincount(ref.astype(int), minlength=k) / len(ref)
    from scipy.spatial.distance import jensenshannon
    return dict(wasserstein=stats.wasserstein_distance(x, ref),
                ks=stats.ks_2samp(x, ref).statistic, js=jensenshannon(px, pr, base=2) ** 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--model", default="openai/gpt-4o-mini")
    ap.add_argument("--provider", default=None, help="pin an OpenRouter provider for reproducibility")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--conditions", default="ABCD")
    ap.add_argument("--alpha", type=float, default=REF_ALPHA, help="gamma heterogeneity for D")
    ap.add_argument("--anchor", action="store_true",
                    help="tell the persona the retailer's base purchase rate (prompt variant)")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="pilot_out")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    pers = make_personas(a.n, rng)
    ref = reference(max(a.n * 20, 5000), rng)
    mock = MockLLM(rng)
    rows = []
    for cond in a.conditions:
        for rep in range(a.reps):
            for p in pers.itertuples():
                pr = prompts(p, a.anchor)[cond]
                txt = mock(pr, SEGMENTS[p.segment]) if a.mock else call_llm(a.model, pr, a.temp, a.provider)
                rows.append(dict(cond=cond, rep=rep, id=p.id, segment=p.segment,
                                 raw=txt, count=parse(cond, txt, rng, a.alpha)))
                if not a.mock and (p.id + 1) % 10 == 0:
                    print(f"  cond {cond} rep {rep}: {p.id + 1}/{a.n} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.out, "raw_counts.csv"), index=False)
    out = [dict(cond="real(ref)", **summarize(ref))]
    for cond, g in df.groupby("cond"):
        ok = g["count"].dropna()
        row = dict(cond=cond, parse_fail=1 - len(ok) / len(g))
        if len(ok) > 5:
            x = ok.astype(float).values
            row.update(summarize(x)); row.update(distances(x, ref))
            row["zero_expected_at_mean"] = zero_at_mean(x.mean())
        out.append(row)
    seg = df.dropna(subset=["count"]).pivot_table(index="segment", columns="cond", values="count", aggfunc="mean")
    seg.to_csv(os.path.join(a.out, "segment_means.csv"))
    res = pd.DataFrame(out)
    res.to_csv(os.path.join(a.out, "summary.csv"), index=False)
    print(res.round(3).to_string(index=False))
    print("\nmean count by segment (does the LLM differentiate personas?)")
    print(seg.round(2).to_string())


if __name__ == "__main__":
    main()
