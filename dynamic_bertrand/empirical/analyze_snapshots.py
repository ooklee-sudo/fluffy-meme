"""Analyse the prospective OpenRouter panel (snapshots.csv) once enough days have accumulated.

Computes, per (model, provider endpoint), the number of days observed and the number of price changes (repricing frequency),
the direction of changes, the response lag of other providers after a price cut (matching behaviour, Proposition 4), and a
cross-sectional regression of the log price relative to the model-day median on the provider's repricing frequency, with model-day fixed effects.
It refuses to run on fewer than 28 distinct days.

python analyze_snapshots.py
"""
import collections, csv, os, statistics as st
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "snapshots.csv"))))
    days = sorted(set(r["date"] for r in rows))
    print("distinct days:", len(days), days[0], days[-1])
    if len(days) < 28:
        print("Need at least 28 distinct days of snapshots; keep collect_openrouter.py running daily.")
        return
    series = collections.defaultdict(dict)                         # (model, provider, tag) -> date -> blended price
    for r in rows:
        if not r["prompt_per_m"]:
            continue
        i, o = float(r["prompt_per_m"]), float(r["completion_per_m"] or r["prompt_per_m"])
        series[(r["model_id"], r["provider"], r["tag"])][r["date"]] = (3 * i + o) / 4
    freq, changes = {}, collections.defaultdict(list)
    for k, s in series.items():
        ds = sorted(s)
        ch = [(b, s[b] / s[a] - 1) for a, b in zip(ds, ds[1:]) if abs(s[b] / s[a] - 1) > 0.005]
        freq[k] = len(ch) / max(len(ds) - 1, 1)
        changes[k[0]].extend((d, k[1], x) for d, x in ch)
    # response lag after a cut: days until another provider of the same model also cuts
    lags = []
    for m, ev in changes.items():
        cuts = sorted((d, p) for d, p, x in ev if x < 0)
        for d, p in cuts:
            later = [d2 for d2, p2 in cuts if p2 != p and d2 > d]
            if later:
                lags.append((np.datetime64(later[0]) - np.datetime64(d)).astype(int))
    print("median days to the next cut by another provider of the same model:", np.median(lags) if lags else None, "n =", len(lags))
    # regression
    cell = collections.defaultdict(list)
    for k, s in series.items():
        for d, v in s.items():
            cell[(k[0], d)].append((k, v))
    X, Y = [], []
    for (m, d), L in cell.items():
        if len(L) < 4:
            continue
        med = st.median(v for _, v in L)
        xs = [freq[k] for k, _ in L]; ys = [np.log(v / med) for _, v in L]
        X += list(np.array(xs) - np.mean(xs)); Y += list(np.array(ys) - np.mean(ys))
    X, Y = np.array(X), np.array(Y)
    print("coefficient (log relative price per unit daily repricing rate):", float(X @ Y / (X @ X)), "n =", len(X))


if __name__ == "__main__":
    main()
