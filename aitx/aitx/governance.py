"""Free, rule-based proxies for loss aversion (lambda) and CIO power (theta) from SEC filings.

lambda (primary): goodwill-impairment delay in the spirit of Ramanna and Watts (2012). A fiscal year
    signals impairment when the firm carries goodwill and either its public float (market value of
    equity held by non-affiliates, from the 10-K cover page) is below book equity or the public float fell
    by at least 20 percent from the prior year. lambda is the share of signal years, FY2015-FY2022, in
    which no goodwill impairment loss was recognized; undefined without a signal year.
lambda (secondary): loss-framed language, the share of Loughran-McDonald (2011) negative words in the
    MD&A of the 10-K filed in calendar 2022 (the manuscript's call-transcript measure moved to a free
    source).
theta: CIO power index from filings made in calendar 2022 (before generative-AI adoption decisions),
    the mean of three indicators: a chief information/technology/digital officer is listed among the
    executive officers (top management team), that officer's title is executive vice president or
    higher, and a filing states that the officer reports to the chief executive.
"""
import json
import re

import pandas as pd

from . import sec

YEARS = range(2015, 2023)
CIO = re.compile(r"Chief\s+(?:Information|Technology|Digital)(?:\s+(?:and|&)\s+[A-Z][a-z]+)*\s+Officer|"
                 r"\bCIO\b|\bCTO\b")
SENIOR = re.compile(r"Executive\s+Vice\s+President|\bEVP\b|(?<!Vice )\bPresident\b")
EXEC_HEAD = re.compile(r"(?:Information\s+about\s+(?:our\s+)?|Our\s+)?Executive\s+Officers\b", re.I)
REPORTS_CEO = re.compile(r"report(?:s|ing)?\s+(?:directly\s+)?to\s+(?:the\s+|our\s+)?"
                         r"(?:Chief\s+Executive\s+Officer|CEO)", re.I)


# ------------------------------------------------------------------ lambda
def _annual(facts, taxonomy, tag):
    """{fiscal-year-end year: value} from 10-K facts, the latest filing winning for each period end."""
    units = facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get("USD", [])
    by_end = {}
    for u in units:
        if u.get("form") not in ("10-K", "10-K/A") or "end" not in u:
            continue
        if "start" in u:  # flow items: keep full-year periods only
            days = (pd.Timestamp(u["end"]) - pd.Timestamp(u["start"])).days
            if not 330 <= days <= 400:
                continue
        prev = by_end.get(u["end"])
        if prev is None or u.get("filed", "") > prev.get("filed", ""):
            by_end[u["end"]] = u
    out = {}
    for end, u in sorted(by_end.items()):
        out[int(end[:4])] = float(u["val"])  # later period end in the same year overwrites
    return out


def impairment_delay(companyfacts, years=YEARS, decline=0.2):
    facts = companyfacts.get("facts", {})
    gw = _annual(facts, "us-gaap", "Goodwill")
    imp = _annual(facts, "us-gaap", "GoodwillImpairmentLoss")
    eq = _annual(facts, "us-gaap", "StockholdersEquity") or _annual(
        facts, "us-gaap", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")
    pf = _annual(facts, "dei", "EntityPublicFloat")
    signal = delay = 0
    for y in years:
        below_book = eq.get(y, 0) > 0 and y in pf and pf[y] < eq[y]
        fell = y in pf and y - 1 in pf and pf[y] <= (1 - decline) * pf[y - 1]
        if gw.get(y, 0) > 0 and (below_book or fell):
            signal += 1
            delay += imp.get(y, 0) <= 0
    return {"gw_years": sum(1 for y in years if gw.get(y, 0) > 0), "signal_years": signal,
            "delay_years": delay, "lam": delay / signal if signal else None}


MDNA = re.compile(r"Item\s*7\s*[.:\-–—]?\s*Management.s\s+Discussion\s+and\s+Analysis", re.I)
MDNA_END = re.compile(r"Item\s*7A\s*[.:\-–—]?\s*Quantitative|Item\s*8\s*[.:\-–—]?\s*Financial\s+Statements", re.I)


def mdna_text(text):
    """MD&A of a 10-K: the longest Item 7 -> Item 7A/8 span, which skips the table of contents."""
    best = ""
    for m in MDNA.finditer(text):
        end = MDNA_END.search(text, m.end())
        span = text[m.end(): end.start() if end else m.end() + 200000]
        if len(span) > len(best):
            best = span
    return best


def negative_share(text, negative_words):
    """Share of Loughran-McDonald negative words among all words (in percent)."""
    words = re.findall(r"[A-Za-z]+", text.upper())
    return 100.0 * sum(w in negative_words for w in words) / len(words) if words else None


def lm_negative_words():
    """Negative word list from the Loughran-McDonald master dictionary bundled with pysentiment2."""
    import os
    import pysentiment2
    path = os.path.join(os.path.dirname(pysentiment2.__file__), "static", "LM.csv")
    lm = pd.read_csv(path)
    return set(lm.loc[lm["Negative"] != 0, "Word"].astype(str).str.upper())


# ------------------------------------------------------------------ theta
def exec_section(text, width=8000):
    """Text of the executive-officers list in a 10-K (the occurrence with most officer titles)."""
    best = ""
    for m in EXEC_HEAD.finditer(text):
        seg = text[m.start(): m.start() + width]
        if len(re.findall(r"Chief\s+\w+\s+Officer|Vice\s+President", seg)) > len(
                re.findall(r"Chief\s+\w+\s+Officer|Vice\s+President", best)):
            best = seg
    return best


def cio_power(tenk_text, proxy_text=""):
    sect = exec_section(tenk_text)
    m = CIO.search(sect)
    tmt = m is not None
    evp = False
    if m:
        around = sect[max(0, m.start() - 120): m.end() + 60]
        evp = bool(SENIOR.search(around))
    reports = False
    for text in (tenk_text, proxy_text):
        for c in CIO.finditer(text or ""):
            if REPORTS_CEO.search(text[max(0, c.start() - 300): c.end() + 300]):
                reports = True
                break
    return {"cio_tmt": int(tmt), "cio_evp": int(evp), "cio_reports_ceo": int(reports),
            "theta": (int(tmt) + int(evp) + int(reports)) / 3,
            "cio_title": re.sub(r"\s+", " ", sect[max(0, m.start() - 80): m.end()]) if m else ""}


def filing_url_in_year(client, cik, form, year):
    """Primary document of the latest `form` filed in calendar `year`, or None."""
    sub = sec.submissions(client, cik)
    blocks = [sub.get("filings", {}).get("recent", {})]
    for f in sub.get("filings", {}).get("files", []):
        st, body = client.get("https://data.sec.gov/submissions/" + f["name"])
        if st == 200:
            blocks.append(json.loads(body))
    best = None
    for b in blocks:
        for fm, d, adsh, doc in zip(b.get("form", []), b.get("filingDate", []),
                                    b.get("accessionNumber", []), b.get("primaryDocument", [])):
            if fm == form and d.startswith(str(year)) and (best is None or d > best[0]):
                best = (d, adsh, doc)
    return sec.document_url(cik, best[1], best[2]) if best else None
