#!/usr/bin/env python3
"""Stage 2 census verification for "Administered Ethics" (Appendix B.4).

Reads the keyword list from the Stage2_Template sheet of the supplement,
runs each keyword in the PIPC decision database (위원회 결정문) through the
site's own search UI (a real browser, so session-bound pagination works),
and writes back:

  Stage2_Template : Hits (n), Date searched, Note        (per keyword)
  Stage2_Hits     : every hit (keyword, date, title, link, Stage-1 flag)
  Stage2_Unique   : hits de-duplicated across keywords, for screening

Screening against B.1 (eligibility) and assigning new RecIDs stays manual:
the script never edits Screening_Log, "New eligible entries" or "Screened by".

Setup:
    pip install playwright openpyxl && playwright install chromium
Usage:
    python stage2_pipc_census.py --xlsx Supplement_Extended_Corpus_Protocol_Log.xlsx
    python stage2_pipc_census.py --xlsx ... --manual     # type hit counts yourself
    python stage2_pipc_census.py --xlsx ... --only 얼굴 홍채   # re-run some keywords

NOTE: the CSS selectors below were NOT verified against the live site (it was
unreachable when this was written). Run once with --headed --debug, inspect
the page, and adjust SELECTORS / BOARD_URL if needed.
"""
import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

# --- adjust to the live site -------------------------------------------------
BOARD_URL = "https://www.pipc.go.kr/np/cop/bbs/selectBoardList.do?bbsId=BS074&mCode=E030010000"
SELECTORS = {
    "keyword":   "input[name='searchKrwd']",       # keyword box
    "field":     "select[name='searchCnd']",       # search field (제목+내용)
    "date_from": "input[name='startDt']",
    "date_to":   "input[name='endDt']",
    "meeting":   "select[name='mtgType']",         # meeting type (전체)
    "submit":    "button:has-text('검색'), a:has-text('검색')",
    "rows":      "table tbody tr",                 # result rows
    "next":      "a.next, a:has-text('다음'), .paging a.next",
}
TOTAL_RE = re.compile(r"(?:총|전체)\s*[:：]?\s*([\d,]+)\s*건")
MAX_PAGES = 50
# -----------------------------------------------------------------------------

HDR_ROW = 2          # header row in Stage2_Template (row 1 is the legend)
FILL = PatternFill("solid", fgColor="FFF2CC")


def load_keywords(ws, only):
    """Rows below the header with a keyword, skipping the example row."""
    out = []
    for r in range(HDR_ROW + 1, ws.max_row + 1):
        kw = ws.cell(r, 1).value
        if not kw or ws.cell(r, 11).value == "Example only":
            continue
        if only and kw not in only:
            continue
        out.append(dict(
            row=r, kw=str(kw), field=ws.cell(r, 2).value or "제목+내용",
            d_from=str(ws.cell(r, 3).value), d_to=str(ws.cell(r, 4).value),
            meeting=ws.cell(r, 5).value or "전체"))
    return out


def stage1_dates(wb):
    """Decision dates already in Screening_Log -> RecIDs (YYYY-MM-DD only)."""
    ws = wb["Screening_Log"]
    m = {}
    for rid, _, date, *_ in ws.iter_rows(min_row=2, values_only=True):
        if date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
            m.setdefault(str(date), []).append(rid)
    return m


def try_select(page, sel, label):
    try:
        page.select_option(sel, label=label, timeout=3000)
    except Exception:
        print(f"    ! could not set {sel} = {label!r}; check manually", file=sys.stderr)


def run_search(page, q):
    page.goto(BOARD_URL, wait_until="networkidle")
    page.fill(SELECTORS["keyword"], q["kw"])
    try_select(page, SELECTORS["field"], q["field"])
    try_select(page, SELECTORS["meeting"], q["meeting"])
    page.fill(SELECTORS["date_from"], q["d_from"])
    page.fill(SELECTORS["date_to"], q["d_to"])
    page.click(SELECTORS["submit"])
    page.wait_for_load_state("networkidle")


def scrape(page):
    """Return (reported_total, hits). Follows the site's own pagination."""
    m = TOTAL_RE.search(page.inner_text("body"))
    total = int(m.group(1).replace(",", "")) if m else None
    hits, seen = [], set()
    for _ in range(MAX_PAGES):
        for tr in page.query_selector_all(SELECTORS["rows"]):
            cells = [c.inner_text().strip() for c in tr.query_selector_all("td")]
            if not cells:
                continue
            a = tr.query_selector("a")
            href = a.get_attribute("href") if a else ""
            if href and href.startswith("/"):
                href = "https://www.pipc.go.kr" + href
            date = next((c for c in cells if re.fullmatch(r"\d{4}[-.]\d{2}[-.]\d{2}", c)), "")
            title = max(cells, key=len)
            key = (title, date)
            if key in seen:
                continue
            seen.add(key)
            hits.append(dict(date=date.replace(".", "-"), title=title,
                             link=href or "", cells=" | ".join(cells)))
        nxt = page.query_selector(SELECTORS["next"])
        if not nxt or (total is not None and len(hits) >= total):
            break
        before = len(hits)
        nxt.click()
        page.wait_for_load_state("networkidle")
        if len(hits) == before and not page.query_selector_all(SELECTORS["rows"]):
            break
    return total, hits


def manual_prompt(q):
    print(f"\n[manual] Search '{q['kw']}' ({q['field']}, {q['d_from']}~{q['d_to']}, {q['meeting']}) in the DB.")
    n = input("  Hits (n): ").strip()
    return (int(n) if n.isdigit() else None), []


def sheet(wb, name, header):
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    return ws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", help="default: <xlsx stem>_stage2.xlsx")
    ap.add_argument("--manual", action="store_true", help="no browser; type hit counts")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--debug", action="store_true", help="pause after each search")
    ap.add_argument("--only", nargs="*", help="run only these keywords")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between searches")
    a = ap.parse_args()

    src = Path(a.xlsx)
    out = Path(a.out) if a.out else src.with_name(src.stem + "_stage2.xlsx")
    wb = openpyxl.load_workbook(src)          # keeps the Flow/Screening formulas
    tpl = wb["Stage2_Template"]
    queries = load_keywords(tpl, a.only)
    s1 = stage1_dates(wb)
    today = dt.date.today().isoformat()
    print(f"{len(queries)} keywords to run")

    hits_ws = sheet(wb, "Stage2_Hits", ["Keyword", "Decision date", "Title", "Link",
                                        "Stage-1 RecID(s) with same date", "Raw row"])
    uniq = {}

    pw = browser = page = None
    if not a.manual:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=not (a.headed or a.debug))
        page = browser.new_page()

    try:
        for q in queries:
            print(f"- {q['kw']}")
            note = "auto"
            try:
                if a.manual:
                    total, hits = manual_prompt(q)
                    note = "manual count"
                else:
                    run_search(page, q)
                    if a.debug:
                        input("  [debug] inspect the page, then press Enter...")
                    total, hits = scrape(page)
                    if total is not None and total != len(hits):
                        note = f"auto; reported {total}, scraped {len(hits)} - verify"
            except Exception as e:                      # keep going, flag the row
                total, hits, note = None, [], f"FAILED: {type(e).__name__}: {e}"[:200]
                print("   ", note, file=sys.stderr)

            r = q["row"]
            tpl.cell(r, 6).value = total if total is not None else len(hits) or None
            tpl.cell(r, 10).value = today
            tpl.cell(r, 11).value = note
            for c in (6, 10, 11):
                tpl.cell(r, c).fill = FILL

            for h in hits:
                flag = ", ".join(s1.get(h["date"], []))
                hits_ws.append([q["kw"], h["date"], h["title"], h["link"], flag, h["cells"]])
                u = uniq.setdefault((h["date"], h["title"]),
                                    dict(h, kws=[], flag=flag))
                u["kws"].append(q["kw"])
            print(f"    hits={total}  scraped={len(hits)}")
            time.sleep(a.delay)
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()

    u_ws = sheet(wb, "Stage2_Unique", ["Decision date", "Title", "Link", "Keywords matched",
                                       "Stage-1 RecID(s) same date",
                                       "Eligible? (Y/N/PEND)", "Reason code", "New RecID", "Screened by"])
    for (d, t), u in sorted(uniq.items(), reverse=True):
        u_ws.append([d, t, u["link"], "; ".join(u["kws"]), u["flag"]])

    wb.save(out)
    print(f"\nSaved {out}\nUnique decisions across keywords: {len(uniq)}")
    print("Next: screen Stage2_Unique against B.1, then add new RecIDs to Screening_Log by hand.")


if __name__ == "__main__":
    main()
