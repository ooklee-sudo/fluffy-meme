"""Pilot: do LLM synthetic customers reproduce real purchase-count distributions?

Conditions (Section 3.1 of the proposal):
  A direct   - ask for the 4-week purchase count
  B daily    - ask for 7 daily 0/1 values per week, 4 calls per customer, then sum
  C describe - ask for P(0..5+) and sample with an external RNG
  D hybrid   - LLM gives a contextual mean lambda_i; an external gamma multiplier
               injects the REMAINING heterogeneity (alpha_within, see below)

Usage (single configuration):
  python run_pilot.py --mock --n 200                     # no key needed
  set OPENROUTER_API_KEY=...                             # Windows cmd
  python run_pilot.py --n 50 --model openai/gpt-4o-mini --anchor
For the full grid (models x temperatures x anchor) use run_all.py.
"""
import argparse, json, os, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from scipy import stats

# Retail II reference (proposal Section 4): mean 0.49, zero 0.73, alpha 3.05
REF_MEAN, REF_ALPHA = 0.49, 3.05
SEGMENTS = {  # segment -> relative mean multiplier (used only by MockLLM)
    "occasional gift buyer": 0.5, "regular small retailer": 1.6,
    "seasonal hobbyist": 0.8, "one-time bargain hunter": 0.3,
}
ANCHOR = (" Context: customers of this retailer make on average about 0.5 purchases "
          "per 4 weeks, and most make none.")


def make_personas(n, rng):
    segs = rng.choice(list(SEGMENTS), size=n)
    return pd.DataFrame({
        "id": range(n), "segment": segs,
        "age": rng.integers(22, 70, n),
        "country": rng.choice(["UK", "Germany", "France", "EIRE"], n, p=[.85, .05, .05, .05]),
    })


def persona_text(p, anchor=False):
    return (f"You are a customer of an online giftware retailer. Profile: {p.segment}, "
            f"age {p.age}, based in {p.country}. You made your first purchase 4 weeks ago."
            + (ANCHOR if anchor else ""))


def reference(n, rng):
    r = 1 / REF_ALPHA
    return rng.negative_binomial(r, r / (r + REF_MEAN), size=n)


# ---------------------------------------------------------------- LLM access
def call_llm(model, prompt, temperature, provider=None, retries=5):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set (or use --mock).")
    key = key.strip().strip('"')
    if not key.isascii() or " " in key:
        sys.exit("OPENROUTER_API_KEY looks invalid (non-ASCII or contains spaces). "
                 "Set it to your real key, e.g. sk-or-v1-...")
    body = {"model": model, "temperature": temperature, "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]}
    if provider:
        body["provider"] = {"order": [provider], "allow_fallbacks": False}
    for i in range(retries):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["choices"][0]["message"]["content"] or ""
        except Exception as e:
            if i == retries - 1:
                print(f"  call failed: {e}", file=sys.stderr)
                return ""
            time.sleep(2 ** (i + 1))


class MockLLM:
    """Implements assumed failure patterns (round numbers, narrow variance). NOT a real LLM."""
    def __init__(self, seed): self.rng = np.random.default_rng(seed + 1)

    def __call__(self, prompt, seg_mult):
        m = REF_MEAN * seg_mult
        if "ONLY an integer" in prompt:
            return str(int(np.clip(round(m + self.rng.normal(0, 0.8)), 0, 6)))
        if "7 comma-separated" in prompt:
            return ",".join(str(int(x)) for x in (self.rng.random(7) < m / 28))
        if "probabilities" in prompt:
            p = np.exp(-np.arange(6) / max(m * 1.2, 0.3)); p /= p.sum()
            return json.dumps(dict(zip(["0", "1", "2", "3", "4", "5+"], p.round(3).tolist())))
        return f"{m:.3f}"


# ---------------------------------------------------------------- conditions
def prompts(p, anchor=False):
    base = persona_text(p, anchor)
    out = {
        "A": base + " How many separate purchases will you make in the next 4 weeks? Answer with ONLY an integer.",
        "C": base + " Give the probabilities of making 0,1,2,3,4,5+ purchases in the next 4 weeks. Reply with ONLY JSON like {\"0\":..,\"1\":..,\"2\":..,\"3\":..,\"4\":..,\"5+\":..} summing to 1.",
        "D": base + " What is your expected average number of purchases per 4 weeks (can be fractional, e.g. 0.4)? Reply with ONLY a number.",
    }
    for w in range(1, 5):
        out[f"B{w}"] = (base + f" Week {w} of the next 4 weeks: for each of its 7 days decide whether you make a "
                        "purchase that day. Reply with ONLY 7 comma-separated 0/1 values.")
    return out


def parse_one(key, text):
    """key: A, B1..B4, C (-> probability vector), D (-> lambda). Returns None on failure."""
    try:
        if key == "A":
            return max(0, int(re.search(r"\d+", text).group()))
        if key.startswith("B"):
            v = [int(x) for x in re.findall(r"[01]", text)][:7]
            return sum(v) if len(v) == 7 else None
        if key == "C":
            d = json.loads(re.search(r"\{.*\}", text, re.S).group())
            pr = np.array([float(d[k]) for k in ["0", "1", "2", "3", "4", "5+"]])
            return pr / pr.sum()
        if key == "D":
            return max(float(re.search(r"\d*\.?\d+", text).group()), 1e-3)
    except Exception:
        return None


def alpha_within(lams, alpha_total):
    """Heterogeneity left for the gamma multiplier once the LLM's lambda_i already vary.

    With lambda = lam_i * g, g ~ Gamma(mean 1, var a_w) independent of lam_i:
    1 + alpha_total = (1 + CV^2(lam_i)) * (1 + a_w)   (avoids double counting).
    """
    c2 = np.var(lams) / np.mean(lams) ** 2
    return max((1 + alpha_total) / (1 + c2) - 1, 0.01), c2


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


# ---------------------------------------------------------------- one configuration
def run(a):
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    pers = make_personas(a.n, rng)
    ref = reference(max(a.n * 20, 5000), rng)
    mock = MockLLM(a.seed)
    seg_mult = {p.id: SEGMENTS[p.segment] for p in pers.itertuples()}

    tasks = []  # (cond, rep, id, key, prompt)
    for cond in a.conditions:
        keys = ["B1", "B2", "B3", "B4"] if cond == "B" else [cond]
        for rep in range(a.reps):
            for p in pers.itertuples():
                pr = prompts(p, a.anchor)
                for k in keys:
                    tasks.append((cond, rep, p.id, k, pr[k]))

    done = [0]

    def work(t):
        txt = mock(t[4], seg_mult[t[2]]) if a.mock else call_llm(a.model, t[4], a.temp, a.provider)
        done[0] += 1
        if not a.mock and done[0] % 200 == 0:
            print(f"  {done[0]}/{len(tasks)} calls done", flush=True)
        return txt

    if a.mock:
        texts = [work(t) for t in tasks]
    else:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            texts = list(ex.map(work, tasks))

    # ---- assemble per-customer counts (sequential: uses the RNG)
    cells = {}
    for t, txt in zip(tasks, texts):
        cells.setdefault((t[0], t[1], t[2]), []).append((t[3], txt))
    rows = []
    for (cond, rep, pid), items in cells.items():
        vals = [parse_one(k, txt) for k, txt in items]
        raw = " | ".join(txt.replace("\n", " ") for _, txt in items)
        cnt = lam = None
        if cond == "A":
            cnt = vals[0]
        elif cond == "B":
            cnt = sum(vals) if all(v is not None for v in vals) else None
        elif cond == "C" and vals[0] is not None:
            cnt = int(rng.choice([0, 1, 2, 3, 4, 5], p=vals[0]))
        elif cond == "D":
            lam = vals[0]
        rows.append(dict(cond=cond, rep=rep, id=pid, segment=pers.segment[pid], raw=raw, lam=lam, count=cnt))
    df = pd.DataFrame(rows)

    info = {}
    d = df.cond == "D"
    if d.any():  # sample D counts per rep after seeing all lambdas -> within-segment alpha
        for rep, g in df[d].groupby("rep"):
            ok = g.lam.notna()
            if ok.sum() > 5:
                a_w, c2 = alpha_within(g.lam[ok].astype(float).values, a.alpha)
                info[f"D_rep{rep}_alpha_within"] = round(float(a_w), 3)
                info[f"D_rep{rep}_cv2_lambda"] = round(float(c2), 3)
                mult = rng.gamma(1 / a_w, a_w, size=ok.sum())
                df.loc[g.index[ok], "count"] = rng.poisson(g.lam[ok].astype(float).values * mult)
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
    res = pd.DataFrame(out)
    res.to_csv(os.path.join(a.out, "summary.csv"), index=False)
    seg = df.dropna(subset=["count"]).pivot_table(index="segment", columns="cond", values="count", aggfunc="mean")
    if d.any():
        seg["D_llm_lambda"] = df[d].groupby("segment").lam.mean()
    seg.to_csv(os.path.join(a.out, "segment_means.csv"))
    json.dump(dict(vars(a), **info), open(os.path.join(a.out, "config.json"), "w"), indent=1)
    return res, seg, info


def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--model", default="openai/gpt-4o-mini")
    ap.add_argument("--provider", default=None, help="pin an OpenRouter provider for reproducibility")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--conditions", default="ABCD")
    ap.add_argument("--alpha", type=float, default=REF_ALPHA, help="total heterogeneity target for D")
    ap.add_argument("--anchor", action="store_true",
                    help="tell the persona the retailer's base purchase rate (prompt variant)")
    ap.add_argument("--workers", type=int, default=8, help="parallel API calls")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="pilot_out")
    return ap


if __name__ == "__main__":
    res, seg, info = run(build_parser().parse_args())
    print(res.round(3).to_string(index=False))
    print("\nmean count by segment (does the LLM differentiate personas?)")
    print(seg.round(2).to_string())
    if info:
        print("\nD heterogeneity split:", info)
