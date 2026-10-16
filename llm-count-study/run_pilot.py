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

# Pooled 4-week basket counts of the 2,469 households in dunnhumby's Complete Journey (2017, 13 windows):
# {count: number of household-windows}. Aggregate histogram only; mean 4.84, zero 0.19, alpha 1.42.
JOURNEY_HIST = {0: 6064, 1: 4385, 2: 3703, 3: 3162, 4: 2706, 5: 2181, 6: 1854, 7: 1417, 8: 1174, 9: 941, 10: 816, 11: 581, 12: 491, 13: 382, 14: 367, 15: 294, 16: 222, 17: 174, 18: 148, 19: 134, 20: 116, 21: 87, 22: 81, 23: 67, 24: 68, 25: 41, 26: 41, 27: 47, 28: 28, 29: 26, 30: 22, 31: 30, 32: 18, 33: 18, 34: 14, 35: 18, 36: 11, 37: 9, 38: 9, 39: 11, 40: 9, 41: 7, 42: 8, 43: 10, 44: 6, 45: 7, 46: 9, 47: 3, 48: 7, 49: 8, 50: 4, 51: 4, 52: 5, 53: 2, 54: 2, 55: 1, 56: 4, 57: 4, 58: 4, 59: 3, 60: 2, 61: 2, 62: 2, 63: 1, 64: 1, 65: 6, 66: 2, 67: 1, 68: 1, 69: 4, 70: 2, 71: 4, 76: 1, 86: 1, 89: 1, 98: 1}

BINS_RETAIL = [("0", 0, 0), ("1", 1, 1), ("2", 2, 2), ("3", 3, 3), ("4", 4, 4), ("5+", 5, 5)]
BINS_GROCERY = [("0", 0, 0), ("1-2", 1, 2), ("3-4", 3, 4), ("5-7", 5, 7), ("8-12", 8, 12),
                ("13-20", 13, 20), ("21+", 21, 35)]

SCENARIOS = {
    # Retail II reference (proposal Section 4): mean 0.49, zero 0.73, alpha 3.05 (parametric NB)
    "retail": dict(
        mean=0.49, alpha=3.05, hist=None, bins=BINS_RETAIL, unit="purchases",
        segments={"occasional gift buyer": 0.5, "regular small retailer": 1.6,
                  "seasonal hobbyist": 0.8, "one-time bargain hunter": 0.3},
        anchor=" Context: customers of this retailer make on average about 0.5 purchases per 4 weeks, "
               "and most make none."),
    # Complete Journey: empirical reference (grocery loyalty households, high mean)
    "grocery": dict(
        mean=None, alpha=None, hist=JOURNEY_HIST, bins=BINS_GROCERY, unit="shopping trips",
        segments={"single-person household": 0.7, "couple without children": 0.9,
                  "family with children": 1.3, "retired household": 1.0},
        anchor=" Context: households in this loyalty program make on average about 5 shopping trips "
               "to the chain per 4 weeks, and some make none."),
}


def get_scenario(name, hist=None):
    sc = dict(SCENARIOS[name], name=name)
    if hist is not None:
        sc["hist"] = hist
    if sc["hist"]:  # exact moments of the empirical reference
        k = np.array(sorted(sc["hist"])); w = np.array([sc["hist"][i] for i in k], float); w /= w.sum()
        m = (k * w).sum(); v = ((k - m) ** 2 * w).sum()
        sc["mean"], sc["alpha"] = m, (v - m) / m**2
        sc["support"], sc["probs"] = k, w
    return sc


def ref_stats(sc):
    m, a = sc["mean"], sc["alpha"]
    if sc["hist"]:
        k, w = sc["support"], sc["probs"]
        v = ((k - m) ** 2 * w).sum()
        return dict(mean=m, var_mean=v / m, zero=w[k == 0].sum(), alpha=a)
    return dict(mean=m, var_mean=1 + a * m, zero=(1 + a * m) ** (-1 / a), alpha=a)


def make_personas(n, rng, sc, seed=0):
    segs = rng.choice(list(sc["segments"]), size=n)
    df = pd.DataFrame({
        "id": range(n), "segment": segs,
        "age": rng.integers(22, 70, n),
        "country": rng.choice(["UK", "Germany", "France", "EIRE"], n, p=[.85, .05, .05, .05]),
    })
    df["hh"] = np.random.default_rng(seed + 7).integers(1, 6, n)  # separate stream: keeps retail runs reproducible
    return df


def load_journey_households():
    """Real Complete Journey households with demographics and their 13 four-week basket counts.

    Reads the parquet files shipped with the `completejourney_py` package (pip install completejourney_py pyarrow),
    or the folder in $JOURNEY_DATA_DIR. Household-level data is not stored in this repository.
    """
    d = os.environ.get("JOURNEY_DATA_DIR")
    if not d:
        import completejourney_py
        d = os.path.join(os.path.dirname(completejourney_py.__file__), "data")
    t = pd.read_parquet(os.path.join(d, "transactions.parquet"))
    demo = pd.read_parquet(os.path.join(d, "demographics.parquet"))
    day = (t.transaction_timestamp.dt.normalize() - pd.Timestamp("2017-01-01")).dt.days
    b = t.assign(day=day).drop_duplicates(["household_id", "basket_id"])[["household_id", "day"]]
    b = b[(b.day >= 0) & (b.day < 364)]
    b["win"] = b.day // 28
    cnt = (b.groupby(["household_id", "win"]).size().unstack(fill_value=0)
           .reindex(index=demo.household_id.values, columns=range(13), fill_value=0))
    return demo.reset_index(drop=True), cnt.values


def demo_text(r):
    """Persona sentence from a household's real demographics (missing fields are left out)."""
    bits = []
    if pd.notna(r.age): bits.append(f"head of household in the age group {r.age}")
    if pd.notna(r.household_comp): bits.append(f"household type: {r.household_comp.lower()}")
    if pd.notna(r.household_size): bits.append(f"{r.household_size} person(s) in the household")
    if pd.notna(r.kids_count): bits.append(f"{r.kids_count} child(ren)")
    if pd.notna(r.marital_status): bits.append(r.marital_status.lower())
    if pd.notna(r.income): bits.append(f"annual household income {r.income}")
    if pd.notna(r.home_ownership): bits.append(r.home_ownership.lower())
    return "Profile: " + ", ".join(bits) + "."


def make_demo_personas(n, demo, counts, seed):
    """n (household, 4-week window) pairs drawn at random; the household's real count in that window is kept."""
    r2 = np.random.default_rng(seed + 11)
    hi, wi = r2.integers(0, len(demo), n), r2.integers(0, counts.shape[1], n)
    rows = demo.iloc[hi].reset_index(drop=True)
    df = pd.DataFrame({"id": range(n), "segment": rows.household_comp.fillna("unknown").values,
                       "household_id": rows.household_id.values, "window": wi, "real_count": counts[hi, wi]})
    df["demo_text"] = [demo_text(r) for r in rows.itertuples()]
    df["mult"] = 0.6 + 0.15 * pd.to_numeric(rows.household_size.str.replace("+", "", regex=False), errors="coerce").fillna(2).values
    return df


def persona_text(sc, p, anchor=False):
    if getattr(p, "demo_text", None):
        base = ("You are a household with a loyalty card at a supermarket chain and you do part of your "
                "grocery shopping there. " + p.demo_text)
    elif sc["name"] == "grocery":
        base = (f"You are a household with a loyalty card at a supermarket chain and you do part of your "
                f"grocery shopping there. Profile: {p.segment}, head of household aged {p.age}, "
                f"{p.hh} person(s).")
    else:
        base = (f"You are a customer of an online giftware retailer. Profile: {p.segment}, "
                f"age {p.age}, based in {p.country}. You made your first purchase 4 weeks ago.")
    return base + (sc["anchor"] if anchor else "")


def reference(n, rng, sc):
    if sc["hist"]:
        return rng.choice(sc["support"], size=n, p=sc["probs"])
    r = 1 / sc["alpha"]
    return rng.negative_binomial(r, r / (r + sc["mean"]), size=n)


# ---------------------------------------------------------------- LLM access
_MODELS = {}


def model_info(model):
    """Ask OpenRouter's public model list whether the model takes `temperature` and can switch reasoning off."""
    if not _MODELS:
        try:
            with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
                for m in json.load(r)["data"]:
                    _MODELS[m["id"]] = m
        except Exception as e:
            print(f"  could not fetch model list ({e}); assuming temperature is supported", file=sys.stderr)
            _MODELS["_failed"] = {}
    m = _MODELS.get(model)
    if not m:
        return dict(temperature=True, reasoning_off=False)
    return dict(temperature="temperature" in m.get("supported_parameters", []),
                reasoning_off="none" in (m.get("reasoning") or {}).get("supported_efforts", []))


def build_body(model, prompt, temperature, max_tokens=300, provider=None):
    info = model_info(model)
    body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if info["temperature"]:
        body["temperature"] = temperature
    if info["reasoning_off"]:
        body["reasoning"] = {"effort": "none"}  # otherwise hidden reasoning can use up max_tokens
    if provider:
        body["provider"] = {"order": [provider], "allow_fallbacks": False}
    return body


def call_llm(model, prompt, temperature, provider=None, retries=5, max_tokens=300):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set (or use --mock).")
    key = key.strip().strip('"')
    if not key.isascii() or " " in key:
        sys.exit("OPENROUTER_API_KEY looks invalid (non-ASCII or contains spaces). "
                 "Set it to your real key, e.g. sk-or-v1-...")
    body = build_body(model, prompt, temperature, max_tokens, provider)
    for i in range(retries):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                ch = json.load(r)["choices"][0]
                # keep the reason in the raw text so parse failures can be diagnosed from raw_counts.csv
                return ch["message"].get("content") or f"[EMPTY finish={ch.get('finish_reason')}]"
        except Exception as e:
            if i == retries - 1:
                print(f"  call failed: {e}", file=sys.stderr)
                return ""
            time.sleep(2 ** (i + 1))


class MockLLM:
    """Implements assumed failure patterns (round numbers, narrow variance). NOT a real LLM."""
    def __init__(self, seed, sc):
        self.rng = np.random.default_rng(seed + 1); self.sc = sc

    def __call__(self, prompt, seg_mult):
        m = self.sc["mean"] * seg_mult
        if "ONLY an integer" in prompt:
            sd = 0.8 if self.sc["name"] == "retail" else 0.8 + 0.2 * m
            return str(int(np.clip(round(m + self.rng.normal(0, sd)), 0, 40)))
        if "7 comma-separated" in prompt:
            return ",".join(str(int(x)) for x in (self.rng.random(7) < m / 28))
        if "probabilities" in prompt:
            if self.sc["name"] == "retail":
                p = np.exp(-np.arange(6) / max(m * 1.2, 0.3)); p /= p.sum()
                return json.dumps(dict(zip([b[0] for b in self.sc["bins"]], p.round(3).tolist())))
            pm = stats.poisson.pmf(np.arange(60), max(m, 0.1))
            p = np.array([pm[lo:hi + 1].sum() for _, lo, hi in self.sc["bins"]]); p /= p.sum()
            return json.dumps(dict(zip([b[0] for b in self.sc["bins"]], p.round(3).tolist())))
        return f"{m:.3f}"


# ---------------------------------------------------------------- conditions
def prompts(sc, p, anchor=False):
    base = persona_text(sc, p, anchor)
    u = sc["unit"]; one = "purchase" if sc["name"] == "retail" else "shopping trip"
    labels = [b[0] for b in sc["bins"]]
    tmpl = "{" + ",".join(f'\"{l}\":..' for l in labels) + "}"
    ex = "e.g. 0.4" if sc["name"] == "retail" else "e.g. 4.5"
    out = {
        "A": base + f" How many separate {u} will you make in the next 4 weeks? Answer with ONLY an integer.",
        "C": base + (f" Give the probabilities of making {', '.join(labels)} {u} in the next 4 weeks. "
                     f"Reply with ONLY JSON like {tmpl} summing to 1."),
        "D": base + f" What is your expected average number of {u} per 4 weeks (can be fractional, {ex})? Reply with ONLY a number.",
    }
    for w in range(1, 5):
        out[f"B{w}"] = (base + f" Week {w} of the next 4 weeks: for each of its 7 days decide whether you make a "
                        f"{one} that day. Reply with ONLY 7 comma-separated 0/1 values.")
    return out


def parse_one(key, text, sc):
    """key: A, B1..B4, C (-> probability vector), D (-> lambda). Returns None on failure."""
    try:
        if key == "A":
            return max(0, int(re.search(r"\d+", text).group()))
        if key.startswith("B"):
            v = [int(x) for x in re.findall(r"[01]", text)][:7]
            return sum(v) if len(v) == 7 else None
        if key == "C":
            d = json.loads(re.search(r"\{.*\}", text, re.S).group())
            pr = np.array([float(d[b[0]]) for b in sc["bins"]])
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


def zero_at_mean(m, alpha):
    """P(0) of an NB with the reference alpha rescaled to mean m: separates mean error from shape error."""
    return (1 + alpha * m) ** (-1 / alpha)


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
    sc = get_scenario(a.scenario)
    if a.personas == "demographic":
        if sc["name"] != "grocery":
            sys.exit("--personas demographic needs --scenario grocery")
        demo, counts = load_journey_households()
        hist = {int(k): int(v) for k, v in zip(*np.unique(counts.ravel(), return_counts=True))}
        sc = get_scenario("grocery", hist)  # reference = real counts of the households that supply the personas
        sc["anchor"] = (f" Context: households in this loyalty program make on average about {sc['mean']:.0f} "
                        "shopping trips to the chain per 4 weeks, and some make none.")
        pers = make_demo_personas(a.n, demo, counts, a.seed)
        seg_mult = {p.id: p.mult for p in pers.itertuples()}
    else:
        pers = make_personas(a.n, rng, sc, a.seed)
        seg_mult = {p.id: sc["segments"][p.segment] for p in pers.itertuples()}
    alpha_target = a.alpha if a.alpha is not None else sc["alpha"]
    ref = reference(max(a.n * 20, 5000), rng, sc)
    mock = MockLLM(a.seed, sc)

    tasks = []  # (cond, rep, id, key, prompt)
    for cond in a.conditions:
        keys = ["B1", "B2", "B3", "B4"] if cond == "B" else [cond]
        for rep in range(a.reps):
            for p in pers.itertuples():
                pr = prompts(sc, p, a.anchor)
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
        vals = [parse_one(k, txt, sc) for k, txt in items]
        raw = " | ".join(txt.replace("\n", " ") for _, txt in items)
        cnt = lam = None
        if cond == "A":
            cnt = vals[0]
        elif cond == "B":
            cnt = sum(vals) if all(v is not None for v in vals) else None
        elif cond == "C" and vals[0] is not None:
            b = sc["bins"][int(rng.choice(len(sc["bins"]), p=vals[0]))]
            cnt = int(b[1]) if b[1] == b[2] else int(rng.integers(b[1], b[2] + 1))
        elif cond == "D":
            lam = vals[0]
        rows.append(dict(cond=cond, rep=rep, id=pid, segment=pers.segment[pid], raw=raw, lam=lam, count=cnt,
                         real_count=pers.real_count[pid] if "real_count" in pers else np.nan))
    df = pd.DataFrame(rows)

    info = {}
    d = df.cond == "D"
    if d.any():  # sample D counts per rep after seeing all lambdas -> within-segment alpha
        for rep, g in df[d].groupby("rep"):
            ok = g.lam.notna()
            if ok.sum() > 5:
                a_w, c2 = alpha_within(g.lam[ok].astype(float).values, alpha_target)
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
            row["zero_expected_at_mean"] = zero_at_mean(x.mean(), sc["alpha"])
        if g.real_count.notna().any():  # individual-level validity: rank correlation with the household's real count
            for col, name in (("count", "rho_real"), ("lam", "rho_lambda_real")):
                gg = g.dropna(subset=[col, "real_count"])
                if len(gg) > 20 and gg[col].nunique() > 1:
                    row[name] = float(stats.spearmanr(gg[col].astype(float), gg.real_count)[0])
        out.append(row)
    res = pd.DataFrame(out)
    res.to_csv(os.path.join(a.out, "summary.csv"), index=False)
    seg = df.dropna(subset=["count"]).pivot_table(index="segment", columns="cond", values="count", aggfunc="mean")
    if d.any():
        seg["D_llm_lambda"] = df[d].groupby("segment").lam.mean()
    seg.to_csv(os.path.join(a.out, "segment_means.csv"))
    json.dump(dict(vars(a), ref=ref_stats(sc), **info), open(os.path.join(a.out, "config.json"), "w"), indent=1)
    return res, seg, info


def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--model", default="openai/gpt-4o-mini")
    ap.add_argument("--provider", default=None, help="pin an OpenRouter provider for reproducibility")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--conditions", default="ABCD")
    ap.add_argument("--alpha", type=float, default=None, help="total heterogeneity target for D (default: scenario's)")
    ap.add_argument("--scenario", choices=["retail", "grocery"], default="retail",
                    help="retail = Retail II (mean ~0.5); grocery = Complete Journey (mean ~4.8)")
    ap.add_argument("--personas", choices=["synthetic", "demographic"], default="synthetic",
                    help="demographic = real Complete Journey households (needs: pip install completejourney_py pyarrow)")
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
