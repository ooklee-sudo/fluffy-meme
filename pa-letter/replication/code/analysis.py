"""Main analyses of the Letter from post- and event-level data.

Reads data/posts.csv and data/events.csv (schemas in data/README.md) and writes:
  output/table1_agreement.csv     Table 1 Panel B: kappa, AC1, precision/recall
  output/table_s2_labelsets.csv   SI Table S2: class means by label set and the
                                  human-minus-model escalation difference
  output/table2_decomposition.csv Table 2 and SI Table S3: equation (2) terms

Run `python analysis.py --demo` to check the pipeline on synthetic data; the
demo numbers mean nothing.
"""
import argparse
import csv
import os
import random
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "output")

CLASSES = ["escalation", "deescalation", "mixed", "other"]
LABEL_SETS = ["model1", "v2_opus", "v2_sonnet", "v2_haiku", "v2_sonnet_repeat", "v2_majority"]
N_BOOT = 10_000
SEED = 20261014


# ---------------------------------------------------------------- agreement
def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in CLASSES) / n**2
    return (po - pe) / (1 - pe)


def gwet_ac1(a, b):
    n, q = len(a), len(CLASSES)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pi = {k: (ca[k] + cb[k]) / (2 * n) for k in CLASSES}
    pe = sum(p * (1 - p) for p in pi.values()) / (q - 1)
    return (po - pe) / (1 - pe)


def kappa_ci(a, b, rng, n_boot=2000):
    idx = np.arange(len(a))
    stats = []
    for _ in range(n_boot):
        s = rng.choice(idx, len(idx))
        stats.append(cohen_kappa([a[i] for i in s], [b[i] for i in s]))
    return np.percentile(stats, [2.5, 97.5])


def precision_recall(pred, truth, cls):
    tp = sum(p == cls and t == cls for p, t in zip(pred, truth))
    npred = sum(p == cls for p in pred)
    ntrue = sum(t == cls for t in truth)
    return tp / npred if npred else float("nan"), tp / ntrue if ntrue else float("nan"), npred


# ---------------------------------------------------------------- events
def signed(ev, cls):
    """30-minute return signed in the direction class `cls` implies (oil up for escalation)."""
    r = float(ev["ret30"])
    return r if cls == "escalation" else -r


def class_events(events, labels, cls):
    return [e for e in events if e[labels] == cls]


def day_cluster_boot_diff(events, cls, labels_a, labels_b, rng):
    """Day-clustered bootstrap of mean(class under a) - mean(class under b)."""
    days = sorted({e["day"] for e in events})
    by_day = defaultdict(list)
    for e in events:
        by_day[e["day"]].append(e)
    draws = []
    for _ in range(N_BOOT):
        sample = [e for d in rng.choice(days, len(days)) for e in by_day[d]]
        a = [signed(e, cls) for e in sample if e[labels_a] == cls]
        b = [signed(e, cls) for e in sample if e[labels_b] == cls]
        if a and b:
            draws.append(np.mean(a) - np.mean(b))
    draws = np.array(draws)
    point = (np.mean([signed(e, cls) for e in class_events(events, labels_a, cls)])
             - np.mean([signed(e, cls) for e in class_events(events, labels_b, cls)]))
    lo, hi = np.percentile(draws, [2.5, 97.5])
    p = 2 * min((draws <= 0).mean(), (draws >= 0).mean())
    return point, lo, hi, min(p, 1.0)


def decomposition(events, labels, cls):
    model_ev = class_events(events, labels, cls)
    human_mean = np.mean([signed(e, cls) for e in class_events(events, "human", cls)])
    n = len(model_ev)
    row = {"class": cls, "label_set": labels, "n_model": n,
           "mean_eq1": np.mean([signed(e, cls) for e in model_ev]), "human_mean": human_mean}
    total = 0.0
    for h in [cls] + [c for c in CLASSES if c != cls]:
        cell = [signed(e, cls) for e in model_ev if e["human"] == h]
        share = len(cell) / n
        term = share * (np.mean(cell) - human_mean) if cell else 0.0
        # "opposite": human escalation in the de-escalation class, and vice versa
        key = "same" if h == cls else ("opposite" if h in ("escalation", "deescalation") else h)
        row[f"{key}_n"] = len(cell)
        row[f"{key}_mean"] = np.mean(cell) if cell else float("nan")
        row[f"{key}_term"] = term
        total += term
    row["gap_eq2"] = total
    assert abs(total - (row["mean_eq1"] - human_mean)) < 1e-9  # identity
    return row


# ---------------------------------------------------------------- io
def read_csv(name):
    with open(os.path.join(DATA, name), newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(name, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as fh:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print(f"wrote {path}")


def make_demo():
    """Synthetic posts and events with the same schema; for pipeline checks only."""
    r = random.Random(SEED)
    posts, events = [], []
    for i in range(191):
        human = r.choices(CLASSES, weights=[28, 46, 34, 83])[0]
        row = {"post_id": f"p{i}", "human": human}
        for ls in LABEL_SETS:
            row[ls] = human if r.random() < 0.6 else r.choice(CLASSES)
        posts.append(row)
    for p in r.sample(posts, 95):
        drift = {"escalation": 0.45, "deescalation": -0.9}.get(p["human"], 0.0)
        events.append({**p, "day": f"d{r.randint(1, 60)}", "ret30": drift + r.gauss(0, 1.0)})
    return posts, events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run on synthetic data")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(SEED)
    posts, events = make_demo() if args.demo else (read_csv("posts.csv"), read_csv("events.csv"))

    # Table 1, Panel B
    truth = [p["human"] for p in posts]
    t1 = []
    for ls in LABEL_SETS:
        pred = [p[ls] for p in posts]
        lo, hi = kappa_ci(truth, pred, rng)
        ep, er, en = precision_recall(pred, truth, "escalation")
        dp, dr, _ = precision_recall(pred, truth, "deescalation")
        t1.append({"label_set": ls, "kappa": cohen_kappa(truth, pred), "kappa_lo": lo, "kappa_hi": hi,
                   "ac1": gwet_ac1(truth, pred), "esc_labels": en, "esc_precision": ep,
                   "esc_recall": er, "deesc_precision": dp, "deesc_recall": dr})
    write_csv("table1_agreement.csv", t1)

    # SI Table S2
    s2 = []
    for ls in ["human"] + LABEL_SETS:
        row = {"label_set": ls}
        for cls in ("deescalation", "escalation"):
            x = [signed(e, cls) for e in class_events(events, ls, cls)]
            row[f"{cls}_n"] = len(x)
            row[f"{cls}_mean"] = float(np.mean(x)) if x else float("nan")
            row[f"{cls}_median"] = float(np.median(x)) if x else float("nan")
            row[f"{cls}_wilcoxon_p"] = float(wilcoxon(x).pvalue) if len(x) >= 6 else float("nan")
        if ls != "human":
            d, lo, hi, p = day_cluster_boot_diff(events, "escalation", "human", ls, rng)
            row.update({"esc_diff_human_minus": d, "diff_lo": lo, "diff_hi": hi, "diff_p": p})
        s2.append(row)
    write_csv("table_s2_labelsets.csv", s2)

    # Table 2 and SI Table S3
    t2 = [decomposition(events, ls, cls) for cls in ("escalation", "deescalation")
          for ls in ("model1", "v2_majority")]
    write_csv("table2_decomposition.csv", t2)


if __name__ == "__main__":
    main()
