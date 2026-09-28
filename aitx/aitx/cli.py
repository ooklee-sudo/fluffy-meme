"""Command-line entry point.

    python -m aitx.cli edgar-search
    python -m aitx.cli edgar-verify [--limit N]
    python -m aitx.cli firm-info
    python -m aitx.cli cc-guess
    python -m aitx.cli cc-collect --ats-map data/ats_map.csv
    python -m aitx.cli build --source edgar|postings
"""
import argparse
import os
from datetime import datetime

import pandas as pd

from . import commoncrawl as cc
from . import keywords as kw
from . import panel
from . import sec
from .config import Config
from .http import Client


def _p(cfg, name):
    os.makedirs(cfg.data_dir, exist_ok=True)
    return os.path.join(cfg.data_dir, name)


def _sec_client(cfg):
    cfg.check()
    return Client(cfg.user_agent, cfg.sec_rps, os.path.join(cfg.cache_dir, "sec"))


def _append_csv(df, path):
    df.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


# ------------------------------------------------------------------ EDGAR
def cmd_edgar_search(cfg, args):
    client = _sec_client(cfg)
    rows = []
    for kind, phrases in kw.SEARCH_PHRASES.items():
        for ph in phrases:
            hits = sec.efts_search(client, ph, cfg.start_date, cfg.end_date, cfg.forms)
            for h in hits:
                h["kind"] = kind
            rows += hits
            print(f"[{kind}] {ph!r}: {len(hits)} hits")
    df = pd.DataFrame(rows)
    df.to_csv(_p(cfg, "edgar_hits.csv"), index=False)
    print(f"saved {len(df)} rows, {df['cik'].nunique()} firms -> edgar_hits.csv")


def cmd_edgar_verify(cfg, args):
    """Download each RAG/FT hit document and apply the context-aware regex rules."""
    client = _sec_client(cfg)
    hits = pd.read_csv(_p(cfg, "edgar_hits.csv"))
    docs = (hits[hits["kind"].isin(["rag", "ft"])]
            .drop_duplicates(["cik", "adsh", "filename"]))
    out_path = _p(cfg, "edgar_docs.csv")
    done = set()
    if os.path.exists(out_path):
        prev = pd.read_csv(out_path)
        done = set(zip(prev["cik"], prev["adsh"], prev["filename"]))
    todo = [r for r in docs.itertuples() if (r.cik, r.adsh, r.filename) not in done]
    if args.limit:
        todo = todo[: args.limit]
    batch = []
    for i, r in enumerate(todo, 1):
        text = sec.fetch_text(client, sec.document_url(r.cik, r.adsh, r.filename))
        res = kw.classify(text)
        batch.append({"cik": r.cik, "name": r.name, "sic": r.sic, "form": r.form,
                      "date": r.file_date, "adsh": r.adsh, "filename": r.filename,
                      "doc_id": f"{r.adsh}:{r.filename}", "text_len": len(text), **res})
        if len(batch) >= 50 or i == len(todo):
            _append_csv(pd.DataFrame(batch), out_path)
            batch = []
            print(f"verified {i}/{len(todo)}")


# ------------------------------------------------------------------ firm info
def cmd_firm_info(cfg, args):
    """Name, SIC, base-year assets, and filing dates."""
    client = _sec_client(cfg)
    docs = pd.read_csv(_p(cfg, "edgar_docs.csv"))
    ciks = sorted(docs.loc[docs["rag"] | docs["ft"], "cik"].unique())
    if os.path.exists(_p(cfg, "ats_map.csv")):
        ciks = sorted(set(ciks) | set(pd.read_csv(_p(cfg, "ats_map.csv"))["cik"]))
    firms, dates = [], []
    for i, cik in enumerate(ciks, 1):
        sub = sec.submissions(client, cik)
        sic = sub.get("sic")
        firms.append({"cik": cik, "name": sub.get("name", ""),
                      "sic": int(sic) if str(sic).isdigit() else None,
                      "assets_base": sec.assets_in_year(client, cik, cfg.base_year)})
        dates += [{"cik": cik, "date": d} for d in sec.filing_dates(client, cik, cfg.forms)]
        if i % 25 == 0:
            print(f"firm info {i}/{len(ciks)}")
    pd.DataFrame(firms).to_csv(_p(cfg, "firms.csv"), index=False)
    pd.DataFrame(dates).to_csv(_p(cfg, "filing_dates.csv"), index=False)
    print(f"saved firms.csv, filing_dates.csv for {len(ciks)} firms")


# ------------------------------------------------------------------ Common Crawl
def _cc_client(cfg):
    ua = cfg.user_agent or "aitx-research-pipeline"
    return Client(ua, cfg.cc_rps, os.path.join(cfg.cache_dir, "cc"))


def cmd_cc_guess(cfg, args):
    """Try slug guesses on the most recent crawl for Greenhouse/Lever/Ashby. Manual check needed."""
    client = _cc_client(cfg)
    firms = pd.read_csv(_p(cfg, "firms.csv"))
    crawls = cc.crawls_between(client, cfg.start_date, cfg.end_date)
    if not crawls:
        raise SystemExit("no Common Crawl crawls found in the study window")
    crawl_id, api = crawls[-1]
    rows = []
    for f in firms.itertuples():
        for slug in cc.slug_candidates(f.name):
            for ats in ("greenhouse", "lever", "ashby"):
                n = sum(len(cc.cdx_query(client, api, pat.format(slug=slug)))
                        for pat in cc.ATS_PATTERNS[ats])
                if n:
                    rows.append({"cik": f.cik, "name": f.name, "ats": ats, "slug": slug,
                                 "captures_in_" + crawl_id: n})
    pd.DataFrame(rows).to_csv(_p(cfg, "ats_candidates.csv"), index=False)
    print("wrote ats_candidates.csv; confirm each row by hand and copy to ats_map.csv "
          "(columns: cik, ats, slug). Add Workday/iCIMS/custom career sites manually.")


def cmd_cc_collect(cfg, args):
    client = _cc_client(cfg)
    amap = pd.read_csv(args.ats_map)
    crawls = cc.crawls_between(client, cfg.start_date, cfg.end_date)
    out_path = _p(cfg, "postings.csv")
    seen = set()
    if os.path.exists(out_path):
        seen = set(pd.read_csv(out_path, usecols=["job_key"])["job_key"])
    for f in amap.itertuples():
        # 1) earliest capture of every job-detail URL across crawls
        first = {}
        for crawl_id, api in crawls:
            for pat in cc.ATS_PATTERNS[f.ats]:
                for row in cc.cdx_query(client, api, pat.format(slug=f.slug)):
                    if not cc.DETAIL[f.ats].search(row["url"]):
                        continue
                    if "html" not in row.get("mime", "html"):
                        continue
                    key = cc.canonical_job_url(row["url"])
                    if key not in first or row["timestamp"] < first[key]["timestamp"]:
                        first[key] = row
        todo = [(k, r) for k, r in first.items() if k not in seen]
        print(f"{f.cik} {f.ats}/{f.slug}: {len(first)} jobs, {len(todo)} new")
        # 2) fetch and classify
        batch = []
        for k, row in todo:
            html = cc.fetch_capture(client, row)
            p = cc.extract_posting(html)
            first_seen = datetime.strptime(row["timestamp"][:8], "%Y%m%d").date().isoformat()
            dp = p["date_posted"]
            date = dp if (dp and "2015-01-01" <= dp <= first_seen) else first_seen
            res = kw.classify(p["title"] + " " + p["text"])
            batch.append({"cik": f.cik, "job_key": k, "url": row["url"], "first_seen": first_seen,
                          "date_posted": dp, "date": date, "title": p["title"],
                          "text_len": p["text_len"], "jsonld": p["jsonld"], **res})
            if len(batch) >= 100:
                _append_csv(pd.DataFrame(batch), out_path); batch = []
        if batch:
            _append_csv(pd.DataFrame(batch), out_path)


# ------------------------------------------------------------------ build
def cmd_build(cfg, args):
    firms = pd.read_csv(_p(cfg, "firms.csv"))
    if args.source == "edgar":
        docs = pd.read_csv(_p(cfg, "edgar_docs.csv"))
        for c in ("rag", "ft", "ai"):
            docs[c] = docs[c].astype(str).str.lower().isin(["true", "1"])
        # one row per filing (main document + exhibits), matching the filing-level denominator
        signals = (docs.groupby(["cik", "adsh", "date"], as_index=False)[["rag", "ft", "ai"]].any()
                   .rename(columns={"adsh": "doc_id"}))
        totals = pd.read_csv(_p(cfg, "filing_dates.csv"))
        hits = pd.read_csv(_p(cfg, "edgar_hits.csv"))
        ai_docs = (hits[hits["kind"] == "ai"].drop_duplicates(["cik", "adsh"])
                   .rename(columns={"file_date": "date"})[["cik", "date", "sic"]])
        sic_map = ai_docs[["cik", "sic"]].drop_duplicates("cik")
        ai_docs = ai_docs[["cik", "date"]]
    else:
        post = pd.read_csv(_p(cfg, "postings.csv"))
        post = post[post["text_len"] >= args.min_text]
        signals = post.rename(columns={"job_key": "doc_id"})[["cik", "date", "doc_id", "rag", "ft", "ai"]]
        totals = post[["cik", "date"]]
        ai_docs = post.loc[post["ai"], ["cik", "date"]]
        sic_map = firms[["cik", "sic"]]
    signals = signals.copy()
    for c in ("rag", "ft", "ai"):
        signals[c] = signals[c].astype(str).str.lower().isin(["true", "1"])
    ev = panel.build_events(signals, cfg.end_date)
    ev = panel.apply_exclusions(ev, firms, cfg.min_assets_usd,
                                panel.SUPPLIER_SIC_SPECS[args.supplier_sic])
    tag = args.source if args.supplier_sic == "baseline" else f"{args.source}_{args.supplier_sic}"
    ev.to_csv(_p(cfg, f"events_{tag}.csv"), index=False)
    risk = ev[(ev["status"] == "at_risk") & (ev["exclusion"] == "")]
    fm = panel.firm_month_panel(risk, signals, totals)
    ind = panel.industry_ai_dynamics(ai_docs, sic_map)
    fm = fm.merge(firms[["cik", "sic"]], on="cik", how="left")
    fm["sic2"] = fm["sic"] // 100
    fm = fm.merge(ind, on=["sic2", "month"], how="left")
    fm.to_csv(_p(cfg, f"firm_month_{tag}.csv"), index=False)
    print(ev.groupby(["status", "exclusion"]).size().to_string())
    print(f"\nanalysis sample: {len(risk)} firms, {int(risk['event'].sum())} transitions, "
          f"{len(fm)} firm-months")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="aitx")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("edgar-search")
    v = sub.add_parser("edgar-verify"); v.add_argument("--limit", type=int, default=0)
    sub.add_parser("firm-info")
    sub.add_parser("cc-guess")
    c = sub.add_parser("cc-collect"); c.add_argument("--ats-map", default="data/ats_map.csv")
    b = sub.add_parser("build")
    b.add_argument("--source", choices=["edgar", "postings"], default="edgar")
    b.add_argument("--min-text", type=int, default=200,
                   help="drop postings with less extracted text (JS-rendered pages)")
    b.add_argument("--supplier-sic", choices=sorted(panel.SUPPLIER_SIC_SPECS), default="baseline",
                   help="SIC ranges for exclusion rule R4 (robustness checks)")
    args = ap.parse_args(argv)
    cfg = Config()
    {"edgar-search": cmd_edgar_search, "edgar-verify": cmd_edgar_verify,
     "firm-info": cmd_firm_info, "cc-guess": cmd_cc_guess, "cc-collect": cmd_cc_collect,
     "build": cmd_build}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
