"""History-persona x model-capability factorial (stage 1). Design D (expected count lambda) plus a small design-A check.

Factors: information level L1 (demographics) / L2 (+ previous window count) / L3 (+ previous three counts and recency) /
L4 (+ categories bought recently); capability: small (gpt-4o-mini, gemini flash-lite) vs large (sonnet-5, gpt-5.6-terra),
two models per level; wording: base and third (third-person). Target household-windows need >= 3 earlier windows.

  python run_history.py --mock --mock-data --n 40 --seeds 0            # dry run, no key and no real data
  python run_history.py --n 300 --seeds 0,1,2 --workers 16            # real run (needs OPENROUTER_API_KEY)
"""
import argparse, os, re
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
import run_pilot as rp
import history_data as hd

MODELS = ["openai/gpt-4o-mini", "google/gemini-3.1-flash-lite", "anthropic/claude-sonnet-5", "openai/gpt-5.6-terra"]
CAP = {"openai/gpt-4o-mini": "small", "google/gemini-3.1-flash-lite": "small", "anthropic/claude-sonnet-5": "large", "openai/gpt-5.6-terra": "large"}


def hist_text(level, w, counts, recency, cats, h, t, third):
    sub = "The household" if third else "You"
    poss = "its" if third else "your"
    if level == 1:
        return ""
    s = f" In the previous 4-week period {sub.lower() if not third else 'the household'} made {counts[h, t-1]} shopping trips to the chain."
    if level >= 3:
        a, b, c = counts[h, t-3], counts[h, t-2], counts[h, t-1]
        r = recency[h, t]
        s = (f" In the previous three 4-week periods (oldest to most recent) {'the household' if third else 'you'} made {a}, {b}, and {c} shopping trips to the chain"
             + (f", and {poss} most recent trip was {int(r)} days before the start of the coming period." if not np.isnan(r) else "."))
    if level >= 4:
        cn = sum((cats[h][k] for k in (t - 3, t - 2, t - 1)), start=type(cats[h][0])())
        top = [c for c, _ in cn.most_common(5)]
        s += f" Product categories {'the household' if third else 'you'} bought most often recently: {', '.join(top)}." if top else ""
    return s


def build_sample(counts, seed, n):
    rng = np.random.default_rng(1000 + seed)
    pairs = [(h, t) for h in range(counts.shape[0]) for t in range(3, 13)]
    sel = rng.choice(len(pairs), size=min(n, len(pairs)), replace=False)
    return [pairs[i] for i in sel]


def parse_num(text, integer=False):
    m = re.search(r"\d*\.?\d+", text or "")
    if not m:
        return np.nan
    v = float(m.group())
    return float(int(v)) if integer else max(v, 1e-3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300); ap.add_argument("--a-n", type=int, default=100)
    ap.add_argument("--seeds", default="0,1,2"); ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--wordings", default="base,third"); ap.add_argument("--levels", default="1,2,3,4")
    ap.add_argument("--temp", type=float, default=0.7); ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--runs", default="runs_history"); ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-data", action="store_true")
    a = ap.parse_args()
    demo, counts, recency, cats = hd.load(a.mock_data)
    sc = rp.get_scenario("grocery")
    os.makedirs(a.runs, exist_ok=True)
    for seed in [int(x) for x in a.seeds.split(",")]:
        sample = build_sample(counts, seed, a.n)
        pd.DataFrame([dict(i=i, hh=int(h), win=int(t), real=int(counts[h, t]), prev1=int(counts[h, t-1]),
                           prev3=int(counts[h, t-3:t].sum()), recency=recency[h, t]) for i, (h, t) in enumerate(sample)]
                     ).to_csv(os.path.join(a.runs, f"sample_s{seed}.csv"), index=False)
        for model in a.models.split(","):
            for wording in a.wordings.split(","):
                for level in [int(x) for x in a.levels.split(",")]:
                    out = os.path.join(a.runs, f"{model.replace('/', '_')}_{wording}_L{level}_s{seed}.csv")
                    if os.path.exists(out):
                        print(out, "(already done, skipped)", flush=True); continue
                    rp.WORDING["name"] = "third" if wording == "third" else "base"
                    tasks = []
                    for i, (h, t) in enumerate(sample):
                        r = demo.iloc[h]
                        p = type("P", (), {})(); p.demo_text = rp.demo_text(r) + hist_text(level, wording, counts, recency, cats, h, t, wording == "third")
                        pr = rp.prompts(sc, p, False)
                        tasks.append((i, "D", pr["D"]))
                        if i < a.a_n:
                            tasks.append((i, "A", pr["A"]))
                    def work(tk):
                        if a.mock:
                            r_ = np.random.default_rng(hash((tk[0], level)) % 2**32)
                            lam = 4 + 0.5 * level * r_.normal() + 0.0
                            return f"{max(lam, 0.2):.1f}" if tk[1] == "D" else str(int(max(0, round(lam))))
                        return rp.call_llm(model, tk[2], a.temp, max_tokens=60)
                    if a.mock:
                        texts = [work(tk) for tk in tasks]
                    else:
                        with ThreadPoolExecutor(max_workers=a.workers) as ex:
                            texts = list(ex.map(work, tasks))
                    rows = [dict(seed=seed, i=tk[0], design=tk[1], model=model, cap=CAP.get(model, "mock"), wording=wording, level=level,
                                 raw=str(tx).replace("\n", " "), value=parse_num(tx, tk[1] == "A")) for tk, tx in zip(tasks, texts)]
                    pd.DataFrame(rows).to_csv(out, index=False)
                    print(out, f"{len(rows)} calls", flush=True)


if __name__ == "__main__":
    main()
