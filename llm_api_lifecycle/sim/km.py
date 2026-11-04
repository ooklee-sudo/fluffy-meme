"""Kaplan-Meier lifetimes (with censoring) and notice-period summaries from lifecycle CSVs."""
import numpy as np, pandas as pd, glob, sys
CUTOFF = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2026-11-04")
COLS = "vendor,platform,model_id,tier,stage_at_release,release_date,announce_date,announce_date_lower,announce_source,shutdown_date,shutdown_status,replacement,release_source,notes".split(",")

def load(paths):
    df = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False) for p in paths], ignore_index=True)
    for c in ["release_date", "announce_date", "shutdown_date"]:
        df[c] = pd.to_datetime(df[c].str.strip().replace("", None), errors="coerce")
    return df

def km(time, event):
    """Return (times, survival) for Kaplan-Meier; time in months."""
    order = np.argsort(time); t = np.asarray(time)[order]; e = np.asarray(event)[order]
    ut = np.unique(t[e == 1]); S = 1.0; ts = [0.0]; ss = [1.0]
    for u in ut:
        n = (t >= u).sum(); d = ((t == u) & (e == 1)).sum()
        S *= 1 - d / n; ts.append(u); ss.append(S)
    return np.array(ts), np.array(ss)

def km_median(time, event):
    ts, ss = km(time, event)
    below = np.where(ss <= 0.5)[0]
    return ts[below[0]] if below.size else np.nan

def lifetimes(df, scheduled_as_event=False):
    d = df[df.release_date.notna()].copy()
    ended = d.shutdown_date.notna() & (d.shutdown_date <= CUTOFF)
    if scheduled_as_event: ended = d.shutdown_date.notna()
    end = np.where(ended, d.shutdown_date, CUTOFF)
    d["months"] = (pd.to_datetime(end) - d.release_date).dt.days / 30.4375
    d["event"] = ended.astype(int)
    return d[d.months > 0]

def boot_median(time, event, B=2000, seed=3):
    rng = np.random.default_rng(seed); n = len(time); time = np.asarray(time); event = np.asarray(event)
    m = [km_median(time[i], event[i]) for i in (rng.integers(0, n, n) for _ in range(B))]
    m = np.array(m); m = m[~np.isnan(m)]
    return np.percentile(m, [2.5, 97.5]) if m.size > B * 0.5 else (np.nan, np.nan)
