"""Task-level bootstrap for the detection-curve tail index k, per model and pooled, and k vs model quality.

Resamples tasks (clusters) with replacement. Sensitivity: drop samples with timeouts / load errors.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from analyze_samples import fit_tail, load, survival_curve

FR = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0])
B = 400
rng = np.random.default_rng(0)


def tables(df):
    models = sorted(df.model.unique())
    tasks = sorted(df.task_id.unique())
    ti = {t: i for i, t in enumerate(tasks)}
    sums = np.zeros((len(models), len(tasks), len(FR)))
    cnt = np.zeros((len(models), len(tasks)))
    ysum = np.zeros((len(models), len(tasks)))
    ns = np.zeros((len(models), len(tasks)))
    for (m, t), d in df.groupby(["model", "task_id"]):
        i, j = models.index(m), ti[t]
        ysum[i, j], ns[i, j] = d.y.sum(), len(d)
        s, n = survival_curve(d, FR)
        if s is not None:
            sums[i, j], cnt[i, j] = s * n, n
    return models, tasks, sums, cnt, ysum, ns


def kfit(sums, cnt):
    if cnt.sum() < 30:
        return np.nan
    return fit_tail(FR, sums.sum(0) / cnt.sum())["heavy_k"]


def run(df, label):
    models, tasks, sums, cnt, ysum, ns = tables(df)
    nT = len(tasks)
    k_hat = np.array([kfit(sums[i], cnt[i]) for i in range(len(models))])
    pooled_hat = kfit(sums.sum(0), cnt.sum(0))
    q_hat = ysum.sum(1) / ns.sum(1)
    rho_hat = spearmanr(q_hat, k_hat, nan_policy="omit")[0]
    kb, pb, rb = [], [], []
    for _ in range(B):
        idx = rng.integers(0, nT, nT)
        ks = np.array([kfit(sums[i][idx], cnt[i][idx]) for i in range(len(models))])
        q = ysum[:, idx].sum(1) / ns[:, idx].sum(1)
        kb.append(ks)
        pb.append(kfit(sums[:, idx].sum(0), cnt[:, idx].sum(0)))
        rb.append(spearmanr(q, ks, nan_policy="omit")[0])
    kb, pb, rb = np.array(kb), np.array(pb), np.array(rb)
    lo, hi = np.nanpercentile(kb, [2.5, 97.5], axis=0)
    rows = [{"set": label, "model": m, "mean_y": q_hat[i], "k": k_hat[i], "k_lo": lo[i], "k_hi": hi[i],
             "eps": 1 / (1 + k_hat[i]), "eps_lo": 1 / (1 + hi[i]), "eps_hi": 1 / (1 + lo[i])} for i, m in enumerate(models)]
    pl, ph = np.nanpercentile(pb, [2.5, 97.5])
    rows.append({"set": label, "model": "POOLED", "mean_y": np.nan, "k": pooled_hat, "k_lo": pl, "k_hi": ph,
                 "eps": 1 / (1 + pooled_hat), "eps_lo": 1 / (1 + ph), "eps_hi": 1 / (1 + pl)})
    r_lo, r_hi = np.nanpercentile(rb, [2.5, 97.5])
    print(f"\n[{label}] samples={len(df):,}")
    out = pd.DataFrame(rows)
    out["model"] = out.model.str.split("/").str[-1]
    print(out.drop(columns="set").round(3).to_string(index=False))
    print(f"Spearman(quality proxy mean_y, k) across models: {rho_hat:.2f}  95% CI [{r_lo:.2f}, {r_hi:.2f}]  "
          f"P(rho<0)={np.mean(rb < 0):.3f}   (rho<0 = worse models have smaller k)")
    return out


def main():
    df = load()
    a = run(df, "all samples")
    clean = df[~df.has_timeout & ~df.load_err]
    b = run(clean, "no timeouts / load errors")
    pd.concat([a, b]).round(4).to_csv("results_bootstrap_k.csv", index=False)


if __name__ == "__main__":
    main()
