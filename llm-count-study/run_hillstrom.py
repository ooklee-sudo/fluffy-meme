"""RQ4 / H4: do LLM synthetic customers reproduce a randomized email promotion effect?

Real benchmark: Hillstrom (2008) MineThatData test, 64,000 customers randomized to no email, men's email,
or women's email; outcomes in the following two weeks: website visit, purchase (conversion).

Synthetic design (within-persona, one independent call per arm so no call sees another arm):
  covariates of N real customers -> persona text -> arm text -> question.
  A_yesno   : "Will you visit / purchase in the next two weeks? Yes or No"   (direct answer)
  C_prob    : "Probability (0-100) that you ..." -> mean elicited probability (no sampling noise)
  C_sampled : Bernoulli draw from the elicited probability with an external RNG
Risk ratio (RR) = rate(email arm) / rate(no email), with paired bootstrap CIs over personas.

  python run_hillstrom.py --mock --n 200                       # no key needed
  python run_hillstrom.py --n 300 --workers 12                 # full grid, needs OPENROUTER_API_KEY
"""
import argparse, json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import run_pilot as rp

URL = "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
ARMS = ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]
OUTCOMES = {"visit": "visit the retailer's website", "purchase": "make a purchase from the retailer"}
# real results from this data set (profile_hillstrom.py): rate in no-email arm, and RR with 95% CI
REAL_BASE = {"visit": 0.1062, "purchase": 0.0057}
REAL_RR = {("visit", "Mens E-Mail"): (1.72, 1.64, 1.81), ("visit", "Womens E-Mail"): (1.43, 1.36, 1.50),
           ("purchase", "Mens E-Mail"): (2.19, 1.77, 2.67), ("purchase", "Womens E-Mail"): (1.54, 1.24, 1.92)}
ANCHOR = (" Context: in a typical two-week period, about 10% of this retailer's customers visit its website "
          "and under 1% make a purchase when they receive no promotional email.")


def load_data(path):
    if not os.path.exists(path):
        print(f"downloading Hillstrom data to {path} ...", flush=True)
        urllib.request.urlretrieve(URL, path)
    return pd.read_csv(path)


def persona(r, anchor):
    kind = {(1, 0): "men's merchandise only", (0, 1): "women's merchandise only", (1, 1): "both men's and women's merchandise"}.get((int(r.mens), int(r.womens)), "no specific merchandise")
    spend = re.sub(r"^\d\)\s*", "", str(r.history_segment))
    area = str(r.zip_code).replace("Surburban", "suburban").lower()
    t = (f"You are a customer of an online retailer that sells men's and women's apparel. Profile: your last purchase "
         f"was {int(r.recency)} month(s) ago; you spent {spend} with the retailer over the past 12 months, buying {kind}; "
         f"you live in a {area} area; you are {'a new customer (first purchase within the past 12 months)' if r.newbie else 'an existing customer'}; "
         f"you usually shop by {str(r.channel).lower()}.")
    return t + (ANCHOR if anchor else "")


def arm_text(arm):
    return {"No E-Mail": " In the next two weeks you receive no promotional email from the retailer.",
            "Mens E-Mail": " In the next two weeks you receive a promotional email from the retailer featuring men's merchandise.",
            "Womens E-Mail": " In the next two weeks you receive a promotional email from the retailer featuring women's merchandise."}[arm]


def question(method, outcome):
    a = OUTCOMES[outcome]
    if method == "A":
        return f" During the next two weeks, will you {a}? Answer with ONLY Yes or No."
    return f" What is the probability, from 0 to 100 percent, that you will {a} during the next two weeks? Reply with ONLY a number."


def mock_llm(rng, method, outcome, arm):
    base = {"visit": 0.12, "purchase": 0.008}[outcome]
    lift = {"No E-Mail": 1.0, "Mens E-Mail": 2.6, "Womens E-Mail": 2.2}[arm]  # assumed exaggeration
    p = min(base * lift, 0.95)
    if method == "A":
        return "Yes" if rng.random() < p * 1.5 else "No"
    return f"{100 * p:.1f}"


def parse(method, text):
    try:
        if method == "A":
            m = re.search(r"\b(yes|no)\b", text, re.I)
            return None if m is None else float(m.group(1).lower() == "yes")
        v = float(re.search(r"\d+(?:\.\d+)?", text).group())
        return min(max(v, 0.0), 100.0) / 100
    except Exception:
        return None


def rr_boot(num, den, B, rng):
    """paired bootstrap of mean(num)/mean(den) over personas with both values."""
    ok = ~(np.isnan(num) | np.isnan(den))
    num, den = num[ok], den[ok]
    if len(num) < 20 or den.mean() == 0:
        return np.nan, np.nan, np.nan
    est = num.mean() / den.mean()
    bs = []
    for _ in range(B):
        i = rng.integers(0, len(num), len(num))
        d = den[i].mean()
        bs.append(num[i].mean() / d if d > 0 else np.nan)
    bs = np.array(bs)
    return est, *np.nanpercentile(bs, [2.5, 97.5])


def run_config(a, data, model, anchor, out):
    rng = np.random.default_rng(a.seed)
    os.makedirs(out, exist_ok=True)
    cust = data.sample(a.n, random_state=a.seed).reset_index(drop=True)
    tasks = []  # (i, method, outcome, arm, prompt)
    for i, r in enumerate(cust.itertuples()):
        p = persona(r, anchor)
        for method in ("A", "C"):
            for outcome in OUTCOMES:
                for arm in ARMS:
                    tasks.append((i, method, outcome, arm, p + arm_text(arm) + question(method, outcome)))
    done = [0]

    def work(t):
        txt = mock_llm(rng, t[1], t[2], t[3]) if a.mock else rp.call_llm(model, t[4], a.temp, max_tokens=60)
        done[0] += 1
        if not a.mock and done[0] % 300 == 0:
            print(f"  {done[0]}/{len(tasks)} calls done", flush=True)
        return txt

    if a.mock:
        texts = [work(t) for t in tasks]
    else:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            texts = list(ex.map(work, tasks))

    cols = {}  # (method, outcome, arm) -> array over personas
    fail = {}
    for t, txt in zip(tasks, texts):
        k = (t[1], t[2], t[3])
        v = parse(t[1], txt)
        cols.setdefault(k, np.full(a.n, np.nan))[t[0]] = np.nan if v is None else v
        fail[k] = fail.get(k, 0) + (v is None)
    rows = []
    for outcome in OUTCOMES:
        for label, method in (("A_yesno", "A"), ("C_prob", "C"), ("C_sampled", "C")):
            def arr(arm):
                x = cols[(method, outcome, arm)].copy()
                if label == "C_sampled":
                    ok = ~np.isnan(x); x[ok] = (rng.random(ok.sum()) < x[ok]).astype(float)
                return x
            ctrl = arr("No E-Mail")
            rec = dict(model=model, anchor=anchor, method=label, outcome=outcome,
                       parse_fail=round(float(np.mean([fail[(method, outcome, m)] for m in ARMS])) / a.n, 3),
                       rate_ctrl=np.nanmean(ctrl))
            for arm in ARMS[1:]:
                x = arr(arm)
                est, lo, hi = rr_boot(x, ctrl, a.boot, rng)
                rec[f"rate_{arm.split()[0].lower()}"] = np.nanmean(x)
                rec[f"RR_{arm.split()[0].lower()}"] = est
                rec[f"RR_{arm.split()[0].lower()}_lo"], rec[f"RR_{arm.split()[0].lower()}_hi"] = lo, hi
            rows.append(rec)
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(out, "hillstrom_summary.csv"), index=False)
    pd.DataFrame({"i": [t[0] for t in tasks], "method": [t[1] for t in tasks], "outcome": [t[2] for t in tasks],
                  "arm": [t[3] for t in tasks], "raw": [x.replace("\n", " ") for x in texts]}).to_csv(
        os.path.join(out, "hillstrom_raw.csv"), index=False)
    json.dump(dict(vars(a), model=model, anchor=anchor), open(os.path.join(out, "config.json"), "w"), indent=1)
    return res


def fmt_rr(e, lo, hi, real):
    if not np.isfinite(e):
        return "n/a"
    star = "*" if np.isfinite(lo) and not (lo <= real <= hi) else ""
    return f"{e:.2f} [{lo:.2f},{hi:.2f}]{star}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--models", default=",".join(["openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "anthropic/claude-haiku-5.5"]))
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data", default="hillstrom.csv")
    ap.add_argument("--runs", default="runs_hillstrom")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    data = load_data(a.data)
    allres = []
    models = ["mock/x"] if a.mock else a.models.split(",")
    for model in models:
        for anchor in (False, True):
            out = os.path.join(a.runs, f"{model.replace('/', '_')}_{'anchor' if anchor else 'plain'}")
            if os.path.exists(os.path.join(out, "hillstrom_summary.csv")):
                print(f"{out} (already done, skipped)", flush=True)
                res = pd.read_csv(os.path.join(out, "hillstrom_summary.csv"))
            else:
                print(f"{out}", flush=True)
                res = run_config(a, data, model, anchor, out)
            allres.append(res)
    res = pd.concat(allres)
    res.to_csv(os.path.join(a.runs, "all_hillstrom.csv"), index=False)
    print("\nREAL (Hillstrom): visit  RR men 1.72 [1.64,1.81], women 1.43 [1.36,1.50]; control rate 0.106")
    print("                  purchase RR men 2.19 [1.77,2.67], women 1.54 [1.24,1.92]; control rate 0.0057")
    print("synthetic RR vs no email, 95% paired-bootstrap CI; * = CI excludes the real RR\n")
    show = []
    for r in res.itertuples():
        show.append(dict(model=r.model, anchor=r.anchor, method=r.method, outcome=r.outcome, fail=r.parse_fail,
                         ctrl=f"{r.rate_ctrl:.3f}",
                         RR_men=fmt_rr(r.RR_mens, r.RR_mens_lo, r.RR_mens_hi, REAL_RR[(r.outcome, "Mens E-Mail")][0]),
                         RR_women=fmt_rr(r.RR_womens, r.RR_womens_lo, r.RR_womens_hi, REAL_RR[(r.outcome, "Womens E-Mail")][0]),
                         men_gt_women=bool(r.RR_mens > r.RR_womens) if np.isfinite(r.RR_mens) and np.isfinite(r.RR_womens) else None))
    print(pd.DataFrame(show).to_string(index=False))


if __name__ == "__main__":
    main()
