"""Build 8-K disclosure event sequences for the S&P 500 constituents from SEC EDGAR (public data).

    python -m semantic_hawkes.build_edgar fetch      # download submissions JSON (cached, ~4 requests/s)
    python -m semantic_hawkes.build_edgar build      # write EasyTPP-format datasets

One sequence per company (CIK). Event = an 8-K filing, timestamped by its EDGAR acceptance time.
Two event definitions are written:
  edgar_8k_filing : one event per filing, type = first substantive item (item 9.01 'exhibits' is administrative)
  edgar_8k_item   : one event per (filing, item); events of the same filing share a timestamp by construction

Caveats: the constituent list is the *current* S&P 500 (survivorship bias); companies are split 80/10/10 into
train/dev/test by a fixed seed; time is measured in days since each company's first event in the window.
"""
import json
import os
import random
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = "semantic_hawkes/real_data/edgar"
UA = "research ooklee@hanyang.ac.kr"
START = "2019-01-01"
MIN_EVENTS = 10
MAX_LEN = 150
MIN_TYPE_COUNT_FRAC = 0.01  # item types rarer than 1% of training events are merged into one 'rare' type

# Official Form 8-K item titles
ITEMS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.04": "Mine Safety Reporting of Shutdowns and Patterns of Violations",
    "1.05": "Material Cybersecurity Incidents",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Continued Listing Rule",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure or Election of Directors or Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.04": "Temporary Suspension of Trading Under Employee Benefit Plans",
    "5.05": "Amendments to the Code of Ethics or Waiver",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Director Nominations",
    "6.01": "ABS Informational and Computational Material",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:  # noqa: BLE001
            time.sleep(2 ** attempt)
            err = e
    raise err


def fetch():
    os.makedirs(f"{ROOT}/raw", exist_ok=True)
    cos = json.load(open(f"{ROOT}/sp500.json"))
    for i, c in enumerate(cos):
        cik = c["CIK"].zfill(10)
        path = f"{ROOT}/raw/{cik}.json"
        if os.path.exists(path):
            continue
        sub = get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        time.sleep(0.25)
        recent = sub["filings"]["recent"]
        rows = [dict(zip(recent.keys(), vals)) for vals in zip(*recent.values())]
        for f in sub["filings"].get("files", []):
            if f["filingTo"] >= START:
                old = get(f"https://data.sec.gov/submissions/{f['name']}")
                time.sleep(0.25)
                rows += [dict(zip(old.keys(), vals)) for vals in zip(*old.values())]
        keep = [dict(filingDate=r["filingDate"], acceptanceDateTime=r["acceptanceDateTime"], form=r["form"],
                     items=r.get("items", "")) for r in rows if r["form"] == "8-K" and r["filingDate"] >= START]
        json.dump(dict(cik=cik, name=sub["name"], symbol=c["Symbol"], filings=keep), open(path, "w"))
        if i % 25 == 0:
            print(i, c["Symbol"], len(keep), flush=True)


def ts(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def build():
    companies = []
    for fn in sorted(os.listdir(f"{ROOT}/raw")):
        d = json.load(open(f"{ROOT}/raw/{fn}"))
        fl = sorted(d["filings"], key=lambda r: r["acceptanceDateTime"])
        companies.append((d["symbol"], fl))
    rng = random.Random(2024)
    order = list(range(len(companies)))
    rng.shuffle(order)
    n = len(order)
    split_of = {}
    for rank, idx in enumerate(order):
        split_of[idx] = "train" if rank < int(0.8 * n) else ("dev" if rank < int(0.9 * n) else "test")

    for variant in ("filing", "item"):
        raw_seqs = []  # (split, [(time_sec, item_code)])
        for idx, (sym, fl) in enumerate(companies):
            ev = []
            for r in fl:
                codes = [c for c in r["items"].split(",") if c]
                codes = [c for c in codes if c != "9.01"] or (["9.01"] if codes else [])
                if not codes:
                    continue
                t = ts(r["acceptanceDateTime"])
                if variant == "filing":
                    ev.append((t, codes[0]))
                else:
                    ev += [(t, c) for c in codes]
            ev = ev[-MAX_LEN:]
            if len(ev) >= MIN_EVENTS:
                raw_seqs.append((split_of[idx], ev))
        # item types: frequent ones keep their name, rare ones are merged
        cnt = {}
        for sp, ev in raw_seqs:
            if sp == "train":
                for _, c in ev:
                    cnt[c] = cnt.get(c, 0) + 1
        total = sum(cnt.values())
        types = sorted(c for c, v in cnt.items() if v / total >= MIN_TYPE_COUNT_FRAC and c in ITEMS)
        rare = "rare"
        names = {c: f"{c} {ITEMS[c]}" for c in types}
        type_ids = {c: i for i, c in enumerate(types)}
        type_ids[rare] = len(types)
        names[rare] = "Other rarely used 8-K items"
        out = {"train": [], "dev": [], "test": []}
        for sp, ev in raw_seqs:
            t0 = ev[0][0]
            ids = [type_ids.get(c, type_ids[rare]) for _, c in ev]
            tt = [(t - t0) / 86400.0 for t, _ in ev]  # days
            dt = [0.0] + [tt[i] - tt[i - 1] for i in range(1, len(tt))]
            inv = {v: k for k, v in type_ids.items()}
            out[sp].append(dict(dim_process=len(type_ids), seq_idx=len(out[sp]), seq_len=len(ev),
                                time_since_start=tt, time_since_last_event=dt, type_event=ids,
                                type_text=[names[inv[i]] for i in ids]))
        d = f"semantic_hawkes/real_data/tppllm/edgar-8k-{variant}"  # same layout as the other text datasets
        os.makedirs(d, exist_ok=True)
        for sp, rows in out.items():
            json.dump(rows, open(f"{d}/{sp}.json", "w"))
        allev = [e for sp in out.values() for r in sp for e in r["type_event"]]
        ties = sum(1 for sp in out.values() for r in sp for x in r["time_since_last_event"][1:] if x == 0)
        print(f"{variant}: K={len(type_ids)} train/dev/test seqs = {[len(out[s]) for s in out]}, "
              f"events={len(allev)}, ties={ties / max(1, len(allev)):.3f}, types={[names[c][:30] for c in type_ids]}")


if __name__ == "__main__":
    {"fetch": fetch, "build": build}[sys.argv[1]]()
