"""Turn document-level signals into the analysis files.

signals: one row per document (filing or posting) with columns
    cik, date (YYYY-MM-DD), doc_id, rag (bool), ft (bool), ai (bool)
totals:  one row per document of any kind (denominator for S), columns cik, date
"""
import numpy as np
import pandas as pd

MONTH = 30.4375


def build_events(signals, censor):
    s = signals.copy()
    s["date"] = pd.to_datetime(s["date"])
    censor = pd.Timestamp(censor)
    s = s[s["date"] <= censor]
    rows = []
    for cik, g in s.groupby("cik"):
        rag_dates = g.loc[g["rag"], "date"]
        ft_dates = g.loc[g["ft"], "date"]
        entry = rag_dates.min() if len(rag_dates) else pd.NaT
        ft_first_date = ft_dates.min() if len(ft_dates) else pd.NaT
        if pd.isna(entry):
            status = "ft_only" if len(ft_dates) else "ai_only"
            rows.append({"cik": cik, "status": status, "entry": pd.NaT, "ft_date": ft_first_date})
            continue
        if pd.notna(ft_first_date) and ft_first_date <= entry:
            rows.append({"cik": cik, "status": "ft_first", "entry": entry, "ft_date": ft_first_date})
            continue
        after = ft_dates[ft_dates > entry]
        ft_date = after.min() if len(after) else pd.NaT
        event = pd.notna(ft_date)
        exit_ = ft_date if event else censor
        rows.append({
            "cik": cik, "status": "at_risk", "entry": entry, "ft_date": ft_date,
            "event": int(event), "exit": exit_,
            "T": max((exit_ - entry).days / MONTH, 0.5),  # half-month floor for same-month exits
            "rag_docs_pre": int(((g["date"] < exit_) & g["rag"]).sum()),
            "cohort": entry.year,
        })
    return pd.DataFrame(rows)


# R4: AI and data infrastructure suppliers, identified from SIC codes alone (no hand coding):
# computer and office equipment (357x), electronic components incl. semiconductors (367x),
# computer programming, data processing, and software (737x)
SUPPLIER_SIC = [(3570, 3579), (3670, 3679), (7370, 7379)]
# alternative ranges for robustness checks (build --supplier-sic NAME)
SUPPLIER_SIC_SPECS = {
    "baseline": SUPPLIER_SIC,
    "narrow": [(7370, 7379)],                                    # software and data processing only
    "broad": SUPPLIER_SIC + [(3660, 3669), (4810, 4819), (4890, 4899), (5045, 5045)],  # + telecom, IT wholesale
    "none": [],                                                  # R4 off
}


def is_supplier_sic(sic, ranges=None):
    ranges = SUPPLIER_SIC if ranges is None else ranges
    return sic.apply(lambda v: pd.notna(v) and any(lo <= v <= hi for lo, hi in ranges))


def apply_exclusions(events, firms, min_assets, supplier_sic=None):
    """Rules: R1 SIC 6770, R2 no base-year assets, R3 assets < min, R4 supplier SIC (SUPPLIER_SIC)."""
    e = events.merge(firms, on="cik", how="left")
    reason = pd.Series("", index=e.index)
    reason[e["sic"] == 6770] = "R1 blank-check company"
    m = (reason == "") & e["assets_base"].isna()
    reason[m] = "R2 no base-year financial statements"
    m = (reason == "") & (e["assets_base"] < min_assets)
    reason[m] = "R3 assets below threshold"
    m = (reason == "") & is_supplier_sic(e["sic"], supplier_sic)
    reason[m] = "R4 supplier industry (SIC)"
    e["exclusion"] = reason
    return e


def firm_month_panel(events, signals, totals):
    """Counting-process panel (start, stop] in months since entry, with lagged time-varying S."""
    ev = events[events["status"] == "at_risk"]
    sig = signals.assign(month=pd.to_datetime(signals["date"]).dt.to_period("M"))
    tot = totals.assign(month=pd.to_datetime(totals["date"]).dt.to_period("M"))
    rag_m = sig[sig["rag"]].groupby(["cik", "month"]).size()
    tot_m = tot.groupby(["cik", "month"]).size()
    out = []
    for _, r in ev.iterrows():
        m0, m1 = r["entry"].to_period("M"), r["exit"].to_period("M")
        months = pd.period_range(m0, m1, freq="M")
        rag = rag_m.get(r["cik"], pd.Series(dtype=float)).reindex(
            pd.period_range(m0 - 240, m1, freq="M"), fill_value=0)
        tt = tot_m.get(r["cik"], pd.Series(dtype=float)).reindex(rag.index, fill_value=0)
        cum_rag, cum_tot = rag.cumsum(), tt.cumsum()
        for k, mo in enumerate(months):
            prev = mo - 1  # lag one month so S is known at the start of the interval
            cr, ct = cum_rag.get(prev, 0), cum_tot.get(prev, 0)
            last = mo == m1
            out.append({
                "cik": r["cik"], "month": str(mo), "start": k, "stop": k + 1,
                "event": int(last and r["event"] == 1),
                "cum_rag": int(cr), "cum_docs": int(ct),
                "S_share": cr / ct if ct else np.nan,
            })
    return pd.DataFrame(out)


def industry_ai_dynamics(ai_docs, sic_map, window=24, min_periods=6):
    """Industry (2-digit SIC) drift mu and volatility sigma of monthly log growth in AI documents.

    Uses information up to month t-1 only.
    """
    d = ai_docs.merge(sic_map, on="cik", how="inner").dropna(subset=["sic"])
    d["sic2"] = (d["sic"] // 100).astype(int)
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M")
    c = d.groupby(["sic2", "month"]).size().unstack(fill_value=0)
    full = pd.period_range(c.columns.min(), c.columns.max(), freq="M")
    c = c.reindex(columns=full, fill_value=0)
    g = np.log1p(c).diff(axis=1)
    mu = g.T.rolling(window, min_periods=min_periods).mean().shift(1).T
    sd = g.T.rolling(window, min_periods=min_periods).std().shift(1).T
    out = (mu.stack().rename("ind_mu").to_frame()
           .join(sd.stack().rename("ind_sigma")).reset_index())
    out.columns = ["sic2", "month", "ind_mu", "ind_sigma"]
    out["month"] = out["month"].astype(str)
    return out
