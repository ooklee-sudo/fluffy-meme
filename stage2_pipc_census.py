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

NOTE: form fields are located by placeholder text and option labels, based on
the page text of the live board; the exact HTML was not available when this was
written. Run once with --debug --only <keyword> and check the output.
"""
import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

# --- site-specific settings --------------------------------------------------
BOARD_URL = "https://pipc.go.kr/np/default/agenda.do?mCode=E030010000"
# Form fields are located by their placeholder text / option labels, not by
# name or id (unknown). Dates are typed as YYYYMMDD, as the site shows them.
DATE_FROM_PH = "input[placeholder*='2022-01-01']"
DATE_TO_PH = "input[placeholder*='2022-12-31']"
KEYWORD_INPUT = ("input[type=text]:not([placeholder*='ex :']), "
                 "input:not([type]):not([placeholder*='ex :'])")
SUBMIT = ("button:has-text('검색'), a:has-text('검색'), input[type=submit], "
          "input[type=button][value*='검색']")
ROWS = "table tbody tr"
PIA_MARK = "침해요인 평가"      # legislative privacy-impact assessments: excluded by protocol
TOTAL_RE = re.compile(r"(?:총|전체)\s*[:：]?\s*([\d,]+)\s*건")
MAX_PAGES = 100
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


def site_date(x):
    return re.sub(r"\D", "", str(x))        # 2020-08-05 -> 20200805


def find_form(page):
    page.locator(DATE_FROM_PH).first.wait_for(timeout=20000)
    f = page.locator("form").filter(has=page.locator(DATE_FROM_PH))
    return f.first if f.count() else page.locator("body")


def pick_option(form, label, exclude_with=None):
    """Select `label` in the <select> that offers it (optionally not the one offering `exclude_with`)."""
    for sel in form.locator("select").all():
        opts = [o.strip() for o in sel.locator("option").all_inner_texts()]
        if label in opts and not (exclude_with and exclude_with in opts):
            sel.select_option(label=label)
            return True
    print(f"    ! no <select> offers {label!r}; set it by hand", file=sys.stderr)
    return False


def set_date(loc, value):
    """Datepicker inputs are often readonly: try typing, else set the value directly."""
    try:
        loc.fill(value, timeout=3000)
        if loc.input_value() == value:
            return
    except Exception:
        pass
    loc.evaluate("""(el, v) => {
        el.removeAttribute('readonly'); el.value = v;
        for (const t of ['input', 'change', 'blur'])
            el.dispatchEvent(new Event(t, {bubbles: true}));
    }""", value)
    if loc.input_value() != value:
        print(f"    ! date field did not take {value!r}; pick it in the calendar by hand", file=sys.stderr)


def run_search(page, q):
    page.goto(BOARD_URL, wait_until="networkidle")
    form = find_form(page)
    kw = form.locator(KEYWORD_INPUT).first
    kw.fill(q["kw"])
    pick_option(form, q["field"])
    pick_option(form, q["meeting"], exclude_with=q["field"])
    set_date(form.locator(DATE_FROM_PH).first, site_date(q["d_from"]))
    set_date(form.locator(DATE_TO_PH).first, site_date(q["d_to"]))
    try:
        form.locator(SUBMIT).last.click(timeout=5000)
    except Exception:
        kw.press("Enter")
    page.wait_for_load_state("networkidle")


def read_rows(page):
    out = []
    for tr in page.locator(ROWS).all():
        cells = [c.strip() for c in tr.locator("td").all_inner_texts()]
        if len(cells) < 4 or not re.fullmatch(r"\d+", cells[0]):
            continue                          # header, "자료가 없습니다", layout rows
        a = tr.locator("a").first
        href = a.get_attribute("href") if a.count() else ""
        if href and href.startswith("/"):
            href = "https://pipc.go.kr" + href
        date = next((c for c in cells if re.fullmatch(r"\d{4}[-.]\d{2}[-.]\d{2}", c)), "")
        out.append(dict(no=int(cells[0]), meeting=cells[1], title=cells[2],
                        date=date.replace(".", "-"), link=href or "",
                        cells=" | ".join(cells)))
    return out


def scrape(page):
    """Return (reported_total_or_None, hits, first_row_number). Follows the site's pagination."""
    m = TOTAL_RE.search(page.inner_text("body"))
    total = int(m.group(1).replace(",", "")) if m else None
    hits, seen, first_no = [], set(), None
    for k in range(1, MAX_PAGES + 1):
        rows = read_rows(page)
        if k == 1 and rows:
            first_no = max(r["no"] for r in rows)
        new = [r for r in rows if (r["no"], r["title"], r["date"]) not in seen]
        if not new:
            break
        for r in new:
            seen.add((r["no"], r["title"], r["date"]))
        hits += new
        nxt = page.get_by_role("link", name=str(k + 1), exact=True)
        if nxt.count() == 0:
            nxt = page.locator("a:has-text('다음'), a.next, a[title*='다음']")
        if nxt.count() == 0:
            break
        nxt.first.click()
        page.wait_for_load_state("networkidle")
    return total, hits, first_no


def manual_prompt(q):
    print(f"\n[manual] Search '{q['kw']}' ({q['field']}, {q['d_from']}~{q['d_to']}, {q['meeting']}) in the DB.")
    n = input("  Hits (n): ").strip()
    return (int(n) if n.isdigit() else None), [], None


def sheet(wb, name, header):
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    return ws


def inspect_site():
    """Dump page structure so SELECTORS can be fixed. Writes inspect_*.html/txt."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=False)
        page = b.new_page()
        page.goto(BOARD_URL)
        print("\n브라우저에서 '위원회 결정문' 검색 화면으로 직접 이동하세요 (메뉴 클릭 OK).")
        print("키워드 '얼굴'로 검색까지 해서 결과 목록이 보이면 여기서 Enter.")
        input("Enter > ")
        lines = [f"URL: {page.url}", f"frames: {[f.url for f in page.frames]}", ""]
        for i, fr in enumerate(page.frames):
            for el in fr.query_selector_all("input, select, button, textarea, a.btn, a[onclick]"):
                try:
                    lines.append(f"frame{i} <{el.evaluate('e => e.tagName')}> "
                                 f"name={el.get_attribute('name')} id={el.get_attribute('id')} "
                                 f"type={el.get_attribute('type')} class={el.get_attribute('class')} "
                                 f"text={el.inner_text()[:30]!r}")
                except Exception:
                    pass
            Path(f"inspect_frame{i}.html").write_text(fr.content(), encoding="utf-8")
        Path("inspect_elements.txt").write_text("\n".join(lines), encoding="utf-8")
        page.screenshot(path="inspect.png", full_page=True)
        b.close()
    print("저장됨: inspect_elements.txt, inspect_frame0.html (+frame N), inspect.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", help="default: <xlsx stem>_stage2.xlsx")
    ap.add_argument("--inspect", action="store_true",
                    help="open the board, let you navigate/search, then dump form + result HTML")
    ap.add_argument("--manual", action="store_true", help="no browser; type hit counts")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--debug", action="store_true", help="pause after each search")
    ap.add_argument("--only", nargs="*", help="run only these keywords")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between searches")
    a = ap.parse_args()

    if a.inspect:
        return inspect_site()

    src = Path(a.xlsx)
    out = Path(a.out) if a.out else src.with_name(src.stem + "_stage2.xlsx")
    wb = openpyxl.load_workbook(src)          # keeps the Flow/Screening formulas
    tpl = wb["Stage2_Template"]
    queries = load_keywords(tpl, a.only)
    s1 = stage1_dates(wb)
    today = dt.date.today().isoformat()
    print(f"{len(queries)} keywords to run")

    hits_ws = sheet(wb, "Stage2_Hits", ["Keyword", "Decision date", "Title", "Link",
                                        "Stage-1 RecID(s) with same date", "Raw row",
                                        "Likely legislative PIA (excluded)"])
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
                    total, hits, first_no = manual_prompt(q)
                    note = "manual count"
                else:
                    run_search(page, q)
                    if a.debug:
                        input("  [debug] inspect the page, then press Enter...")
                    total, hits, first_no = scrape(page)
                    if total is None:
                        total = len(hits)         # site shows no total; count what was scraped
                    elif total != len(hits):
                        note = f"auto; reported {total}, scraped {len(hits)} - verify"
                    if first_no and first_no != len(hits):
                        note += f"; top row no. {first_no} vs scraped {len(hits)} - verify"
            except Exception as e:                      # keep going, flag the row
                total, hits, first_no, note = None, [], None, f"FAILED: {type(e).__name__}: {e}"[:200]
                print("   ", note, file=sys.stderr)

            r = q["row"]
            tpl.cell(r, 6).value = total
            tpl.cell(r, 10).value = today
            tpl.cell(r, 11).value = note
            for c in (6, 10, 11):
                tpl.cell(r, c).fill = FILL

            for h in hits:
                flag = ", ".join(s1.get(h["date"], []))
                pia = "Y" if PIA_MARK in h["title"] else ""
                hits_ws.append([q["kw"], h["date"], h["title"], h["link"], flag, h["cells"], pia])
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
                                       "Stage-1 RecID(s) same date", "Likely legislative PIA (excluded)",
                                       "Eligible? (Y/N/PEND)", "Reason code", "New RecID", "Screened by"])
    for (d, t), u in sorted(uniq.items(), reverse=True):
        u_ws.append([d, t, u["link"], "; ".join(u["kws"]), u["flag"],
                     "Y" if PIA_MARK in t else ""])

    wb.save(out)
    print(f"\nSaved {out}\nUnique decisions across keywords: {len(uniq)}")
    print("Next: screen Stage2_Unique against B.1, then add new RecIDs to Screening_Log by hand.")


if __name__ == "__main__":
    main()
