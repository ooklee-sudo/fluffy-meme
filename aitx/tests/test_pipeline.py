"""Offline tests. Run: python -m unittest discover -s tests -v"""
import gzip
import json
import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aitx import commoncrawl as cc  # noqa: E402
from aitx import keywords as kw  # noqa: E402
from aitx import panel, sec  # noqa: E402


class FakeClient:
    """Routes URLs to canned responses: handler(url, params, headers) -> (status, bytes)."""
    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def get(self, url, params=None, headers=None, ok_status=(200,), cache=True):
        self.calls.append((url, dict(params or {})))
        return self.handler(url, params or {}, headers or {})


# ------------------------------------------------------------------ keywords
class TestKeywords(unittest.TestCase):
    def test_rag_positive(self):
        r = kw.classify("We deployed retrieval-augmented generation over our knowledge base.")
        self.assertTrue(r["rag"]); self.assertFalse(r["ft"])

    def test_rag_acronym_needs_ai_context(self):
        self.assertTrue(kw.classify("Our assistant uses RAG with a large language model.")["rag"])
        self.assertFalse(kw.classify("The RAG was reviewed by the audit committee.")["rag"])

    def test_rag_status_excluded(self):
        self.assertFalse(kw.classify("Project RAG status is green for the AI program.")["rag"])
        self.assertFalse(kw.classify("RAG (red, amber, green) ratings for AI projects.")["rag"])

    def test_fine_tune_needs_model_context(self):
        self.assertTrue(kw.classify("We fine-tuned an open-weight language model on claims data.")["ft"])
        self.assertFalse(kw.classify("We continue to fine-tune our pricing strategy.")["ft"])
        self.assertFalse(kw.classify("We continue to fine-tune our business model.")["ft"])
        self.assertFalse(kw.classify("We fine-tuned our forecasting models.")["ft"])

    def test_fine_tune_negated(self):
        for s in ["RAG lets them ground LLMs on their data without needing to train or fine-tune models.",
                  "Inputs may not be used for the training, retraining, or fine-tuning of AI models.",
                  "Clients prohibit the training, retraining, or fine-tuning of language models on their data.",
                  "There is no large language model training or fine-tuning with client data."]:
            self.assertFalse(kw.classify(s)["ft"], s)
        self.assertTrue(kw.classify("We are not a bank. We fine-tune open-source models such as Llama.")["ft"])

    def test_lora_not_lorawan(self):
        self.assertFalse(kw.classify("Sensors connect over LoRaWAN networks.")["ft"])
        self.assertTrue(kw.classify("We adapt the model with LoRA adapters.")["ft"])

    def test_custom_llm(self):
        r = kw.classify("We are building a proprietary large language model for underwriting.")
        self.assertTrue(r["ft"]); self.assertIn("custom_llm", r["ft_rules"])

    def test_ai_flag(self):
        self.assertTrue(kw.classify("Generative AI may affect demand.")["ai"])


# ------------------------------------------------------------------ SEC
def efts_payload(total, n, start_i=0):
    hits = [{"_id": f"0000000001-24-{start_i + i:06d}:doc{start_i + i}.htm",
             "_source": {"ciks": ["0000000123"], "display_names": ["ACME CORP  (ACME)  (CIK 0000000123)"],
                         "sics": ["7372"], "form": "10-K", "file_date": "2024-02-01",
                         "adsh": f"0000000001-24-{start_i + i:06d}"}} for i in range(n)]
    return json.dumps({"hits": {"total": {"value": total}, "hits": hits}}).encode()


class TestSEC(unittest.TestCase):
    def test_parse_multi_cik(self):
        h = {"_id": "0001-24-1:a.htm", "_source": {"ciks": ["1", "2"], "display_names": ["A", "B"],
                                                 "sics": ["7372", ""], "form": "8-K", "file_date": "2024-01-02"}}
        rows = sec.parse_efts_hit(h, "x")
        self.assertEqual([r["cik"] for r in rows], [1, 2])
        self.assertEqual(rows[0]["sic"], 7372); self.assertIsNone(rows[1]["sic"])
        self.assertEqual(rows[0]["filename"], "a.htm")

    def test_clean_name(self):
        self.assertEqual(sec.clean_name("Couchbase, Inc.  (BASE)  (CIK 0001845022)"), "Couchbase, Inc.")
        self.assertEqual(sec.clean_name("DHC Acquisition Corp.  (BNAI, BNAIW)  (CIK 0001838163)"),
                         "DHC Acquisition Corp.")
        self.assertEqual(sec.clean_name("PRIVATE FILER (CIK 0000000001)"), "PRIVATE FILER")

    def test_pagination(self):
        def h(url, p, hd):
            frm = int(p["from"])
            return 200, efts_payload(150, 100 if frm == 0 else 50, frm)
        c = FakeClient(h)
        rows = sec.efts_search(c, "vector database", "2024-01-01", "2024-03-31", ("10-K",))
        self.assertEqual(len(rows), 150)
        self.assertEqual(c.calls[0][1]["q"], '"vector database"')

    def test_cap_splits_by_month(self):
        def h(url, p, hd):
            if p["startdt"] == "2024-01-01" and p["enddt"] == "2024-03-31":
                return 200, efts_payload(10000, 100)
            return 200, efts_payload(5, 5)
        rows = sec.efts_search(FakeClient(h), "x", "2024-01-01", "2024-03-31", ("10-K",))
        self.assertEqual(len(rows), 15)   # three monthly windows x 5

    def test_assets(self):
        body = json.dumps({"units": {"USD": [
            {"end": "2022-12-31", "val": 5e8, "form": "10-K", "filed": "2023-02-20"},
            {"end": "2022-12-31", "val": 5.1e8, "form": "10-K", "filed": "2024-02-20"},
            {"end": "2023-12-31", "val": 6e8, "form": "10-K", "filed": "2024-02-20"},
            {"end": "2022-09-30", "val": 4e8, "form": "10-Q", "filed": "2022-11-01"}]}}).encode()
        c = FakeClient(lambda u, p, h: (200, body))
        self.assertEqual(sec.assets_in_year(c, 123, 2022), 5.1e8)
        c404 = FakeClient(lambda u, p, h: (404, b""))
        self.assertIsNone(sec.assets_in_year(c404, 123, 2022))

    def test_document_url(self):
        self.assertEqual(sec.document_url(123, "0000000001-24-000001", "a.htm"),
                         "https://www.sec.gov/Archives/edgar/data/123/000000000124000001/a.htm")


# ------------------------------------------------------------------ Common Crawl
def make_warc(html, chunked=False, gz=False):
    body = html.encode()
    if gz:
        body = gzip.compress(body)
    if chunked:
        body = (f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n")
    http = (b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
            + (b"Transfer-Encoding: chunked\r\n" if chunked else b"")
            + (b"Content-Encoding: gzip\r\n" if gz else b"") + b"\r\n" + body)
    warc = (b"WARC/1.0\r\nWARC-Type: response\r\nContent-Length: " + str(len(http)).encode()
            + b"\r\n\r\n" + http + b"\r\n\r\n")
    return gzip.compress(warc)


JOB_HTML = """<html><head><title>ML Engineer</title>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"JobPosting",
"title":"Machine Learning Engineer","datePosted":"2024-05-02",
"description":"<p>Build retrieval-augmented generation pipelines and fine-tune open-weight language models with LoRA.</p>"}
</script></head><body>ignored</body></html>"""


class TestCommonCrawl(unittest.TestCase):
    def test_warc_plain_chunked_gzip(self):
        for chunked in (False, True):
            for gz in (False, True):
                _, body = cc.parse_warc_record(make_warc(JOB_HTML, chunked, gz))
                self.assertIn(b"JobPosting", body, (chunked, gz))

    def test_extract_jsonld(self):
        p = cc.extract_posting(JOB_HTML)
        self.assertTrue(p["jsonld"]); self.assertEqual(p["date_posted"], "2024-05-02")
        r = kw.classify(p["title"] + " " + p["text"])
        self.assertTrue(r["rag"] and r["ft"])

    def test_extract_fallback_text(self):
        p = cc.extract_posting("<html><title>Data Analyst</title><body><p>SQL and Tableau.</p>"
                               "<script>var x=1</script></body></html>")
        self.assertFalse(p["jsonld"]); self.assertIn("SQL and Tableau", p["text"])
        self.assertNotIn("var x", p["text"])

    def test_cdx_paging_and_404(self):
        def h(url, p, hd):
            if p.get("showNumPages"):
                return 200, b'{"pages": 2}'
            line = json.dumps({"url": f"https://boards.greenhouse.io/acme/jobs/{p['page']}",
                               "timestamp": "20240101000000", "filename": "f", "offset": "0",
                               "length": "10", "mime": "text/html"})
            return 200, (line + "\n").encode()
        rows = cc.cdx_query(FakeClient(h), "https://index/x", "boards.greenhouse.io/acme/jobs/*")
        self.assertEqual(len(rows), 2)
        self.assertEqual(cc.cdx_query(FakeClient(lambda u, p, h: (404, b"")), "x", "y"), [])

    def test_fetch_capture_range(self):
        warc = make_warc(JOB_HTML)
        c = FakeClient(lambda u, p, h: (206, warc))
        body = cc.fetch_capture(c, {"filename": "crawl/x.warc.gz", "offset": "100", "length": str(len(warc))})
        self.assertIn(b"JobPosting", body)

    def test_crawls_between(self):
        info = json.dumps([
            {"id": "CC-MAIN-2022-49", "cdx-api": "a", "from": "2022-11-26T00:00:00", "to": "2022-12-10T00:00:00"},
            {"id": "CC-MAIN-2024-10", "cdx-api": "b", "from": "2024-02-20T00:00:00", "to": "2024-03-05T00:00:00"}])
        out = cc.crawls_between(FakeClient(lambda u, p, h: (200, info.encode())), "2023-01-01", "2026-09-29")
        self.assertEqual(out, [("CC-MAIN-2024-10", "b")])

    def test_surt_prefix(self):
        self.assertEqual(cc.surt_prefix("boards.greenhouse.io/acme/jobs/*"), "io,greenhouse,boards)/acme/jobs/")
        self.assertEqual(cc.surt_prefix("www.Acme.com/Careers/*"), "com,acme)/careers/")
        self.assertEqual(cc.surt_prefix("aig.wd1.myworkdayjobs.com/*"), "com,myworkdayjobs,wd1,aig)/")

    def test_cdx_from_index_files(self):
        """Binary search over a fake cluster.idx, then filter the matching cdx blocks."""
        def cdx_line(key, url, status="200"):
            return f"{key} 20240301000000 " + json.dumps(
                {"url": url, "status": status, "mime": "text/html", "filename": "w.warc.gz",
                 "offset": "0", "length": "9"})
        other = [cdx_line(f"com,other{i:05d})/", f"https://other{i:05d}.com/") for i in range(4000)]
        acme = [cdx_line(f"io,greenhouse,boards)/acme/jobs/{i}", f"https://boards.greenhouse.io/acme/jobs/{i}")
                for i in range(5)] + [cdx_line("io,greenhouse,boards)/acme/jobs/9", "x", status="404")]
        tail = [cdx_line(f"io,greenhouse,boards)/zeta/jobs/{i}", "z") for i in range(50)]
        lines = sorted(other + acme + tail)
        cdx, idx, off = b"", "", 0
        for i in range(0, len(lines), 7):             # blocks of 7 lines, one gzip member each
            blk = gzip.compress(("\n".join(lines[i:i + 7]) + "\n").encode())
            idx += f"{lines[i].split(' ')[0]} 20240301000000\tcdx-00000.gz\t{off}\t{len(blk)}\t{i // 7}\n"
            cdx, off = cdx + blk, off + len(blk)
        files = {"cluster.idx": idx.encode(), "cdx-00000.gz": cdx}

        def h(url, p, hd):
            data = files[url.rsplit("/", 1)[1]]
            a, b = map(int, hd["Range"][6:].split("-"))
            return (206, data[a:b + 1]) if a < len(data) else (416, b"")
        rows = cc.cdx_query(FakeClient(h), "files:CC-MAIN-2024-10", "boards.greenhouse.io/acme/jobs/*")
        self.assertEqual(sorted(r["url"] for r in rows),
                         [f"https://boards.greenhouse.io/acme/jobs/{i}" for i in range(5)])
        self.assertEqual(cc.cdx_query(FakeClient(h), "files:CC-MAIN-2024-10", "boards.greenhouse.io/nope/*"), [])

    def test_cdx_falls_back_to_files(self):
        def h(url, p, hd):
            if "index.commoncrawl.org" in url:
                raise RuntimeError("giving up")
            return 416, b""
        try:
            self.assertEqual(cc.cdx_query(FakeClient(h), "https://index.commoncrawl.org/CC-MAIN-2024-10-index",
                                          "boards.greenhouse.io/acme/*"), [])
        finally:
            cc._index_down = False

    def test_crawls_from_files(self):
        page = b"<a>CC-MAIN-2022-49</a><a>CC-MAIN-2024-10</a><a>CC-MAIN-2024-10</a><a>CC-MAIN-2026-39</a>"

        def h(url, p, hd):
            return (500, b"") if "collinfo" in url else (200, page)
        out = cc.crawls_between(FakeClient(h), "2023-01-01", "2026-09-29")
        self.assertEqual(out, [("CC-MAIN-2024-10", "files:CC-MAIN-2024-10"),
                               ("CC-MAIN-2026-39", "files:CC-MAIN-2026-39")])

    def test_helpers(self):
        self.assertEqual(cc.canonical_job_url("https://job-boards.greenhouse.io/acme/jobs/123/"),
                         "boards.greenhouse.io/acme/jobs/123")
        self.assertEqual(cc.slug_candidates("Rocket Companies, Inc."), ["rocketcompanies", "rocket-companies", "rocket"])
        self.assertTrue(cc.DETAIL["greenhouse"].search("https://boards.greenhouse.io/acme/jobs/4012345"))
        self.assertFalse(cc.DETAIL["greenhouse"].search("https://boards.greenhouse.io/acme/jobs"))


# ------------------------------------------------------------------ panel
def toy_signals():
    rows = [
        # firm 1: RAG Jan-2024, FT Jul-2024 -> event
        (1, "2024-01-15", "a", True, False), (1, "2024-03-10", "b", True, False),
        (1, "2024-07-01", "c", False, True),
        # firm 2: RAG Jun-2024, never FT -> censored
        (2, "2024-06-01", "d", True, False),
        # firm 3: FT before RAG -> ft_first
        (3, "2023-05-01", "e", False, True), (3, "2024-01-01", "f", True, False),
        # firm 4: FT only
        (4, "2024-02-01", "g", False, True),
    ]
    s = pd.DataFrame(rows, columns=["cik", "date", "doc_id", "rag", "ft"]); s["ai"] = True
    return s


class TestPanel(unittest.TestCase):
    def test_events(self):
        ev = panel.build_events(toy_signals(), "2024-12-31").set_index("cik")
        self.assertEqual(ev.loc[1, "status"], "at_risk"); self.assertEqual(ev.loc[1, "event"], 1)
        self.assertAlmostEqual(ev.loc[1, "T"], (pd.Timestamp("2024-07-01") - pd.Timestamp("2024-01-15")).days / 30.4375)
        self.assertEqual(ev.loc[1, "rag_docs_pre"], 2)
        self.assertEqual(ev.loc[2, "event"], 0); self.assertEqual(ev.loc[2, "exit"], pd.Timestamp("2024-12-31"))
        self.assertEqual(ev.loc[3, "status"], "ft_first"); self.assertEqual(ev.loc[4, "status"], "ft_only")

    def test_signals_after_censor_ignored(self):
        ev = panel.build_events(toy_signals(), "2024-06-30").set_index("cik")
        self.assertEqual(ev.loc[1, "event"], 0)

    def test_exclusions(self):
        ev = panel.build_events(toy_signals(), "2024-12-31")
        firms = pd.DataFrame({"cik": [1, 2, 3, 4], "sic": [7372, 6770, 6311, 3674],
                              "assets_base": [5e9, 1e8, None, 2e6]})
        e = panel.apply_exclusions(ev, firms, 10e6).set_index("cik")
        self.assertTrue(e.loc[1, "exclusion"].startswith("R4"))
        self.assertTrue(e.loc[2, "exclusion"].startswith("R1"))
        self.assertTrue(e.loc[3, "exclusion"].startswith("R2"))
        self.assertTrue(e.loc[4, "exclusion"].startswith("R3"))

    def test_supplier_sic_specs(self):
        ev = panel.build_events(toy_signals(), "2024-12-31")
        firms = pd.DataFrame({"cik": [1, 2, 3, 4], "sic": [7372, 3663, 6311, 3674],
                              "assets_base": [5e9, 5e9, 5e9, 5e9]})
        r4 = {k: set(panel.apply_exclusions(ev, firms, 10e6, spec).query("exclusion != ''")["cik"])
              for k, spec in panel.SUPPLIER_SIC_SPECS.items()}
        self.assertEqual(r4["none"], set())
        self.assertEqual(r4["narrow"], {1})
        self.assertEqual(r4["baseline"], {1, 4})
        self.assertEqual(r4["broad"], {1, 2, 4})

    def test_firm_month(self):
        s = toy_signals()
        ev = panel.build_events(s, "2024-12-31")
        totals = pd.concat([s[["cik", "date"]], pd.DataFrame({"cik": [1, 1], "date": ["2023-12-01", "2024-02-01"]})])
        fm = panel.firm_month_panel(ev, s, totals)
        f1 = fm[fm["cik"] == 1].reset_index(drop=True)
        self.assertEqual(list(f1["month"]), ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", "2024-07"])
        self.assertEqual(f1["event"].tolist(), [0, 0, 0, 0, 0, 0, 1])
        # January row uses info through Dec-2023: 0 RAG of 1 doc; April row: 2 RAG of 4 docs
        self.assertEqual((f1.loc[0, "cum_rag"], f1.loc[0, "cum_docs"]), (0, 1))
        self.assertEqual((f1.loc[3, "cum_rag"], f1.loc[3, "cum_docs"]), (2, 4))
        self.assertEqual(fm[fm["cik"] == 2]["event"].sum(), 0)
        self.assertNotIn(3, fm["cik"].values)

    def test_industry_dynamics_uses_past_only(self):
        months = pd.period_range("2023-01", "2024-12", freq="M")
        rows = [(1, str(m.to_timestamp().date())) for m in months for _ in range(1 + (m.month % 3))]
        ai = pd.DataFrame(rows, columns=["cik", "date"])
        out = panel.industry_ai_dynamics(ai, pd.DataFrame({"cik": [1], "sic": [7372]}))
        self.assertEqual(set(out["sic2"]), {73})
        first = out.dropna().iloc[0]["month"]
        self.assertGreaterEqual(first, "2023-08")   # needs >= 6 growth obs before t


# ------------------------------------------------------------------ end-to-end build
class TestBuildCLI(unittest.TestCase):
    def test_build_postings(self):
        from aitx import cli
        with tempfile.TemporaryDirectory() as d:
            s = toy_signals()
            post = s.rename(columns={"doc_id": "job_key"}).assign(text_len=500)
            post.to_csv(os.path.join(d, "postings.csv"), index=False)
            pd.DataFrame({"cik": [1, 2, 3, 4], "sic": [5961, 6311, 6311, 3674],
                          "assets_base": [5e9, 1e9, 1e9, 1e9]}).to_csv(os.path.join(d, "firms.csv"), index=False)
            cfg = cli.Config(); cfg.data_dir = d; cfg.end_date = "2024-12-31"

            class A: source = "postings"; min_text = 200; supplier_sic = "baseline"
            cli.cmd_build(cfg, A)
            ev = pd.read_csv(os.path.join(d, "events_postings.csv"))
            fm = pd.read_csv(os.path.join(d, "firm_month_postings.csv"))
            self.assertEqual(int(ev.loc[ev["status"] == "at_risk", "event"].sum()), 1)
            self.assertEqual(fm["event"].sum(), 1)
            self.assertIn("ind_sigma", fm.columns)



class TestBuildEdgar(unittest.TestCase):
    def test_build_edgar(self):
        from aitx import cli
        with tempfile.TemporaryDirectory() as d:
            s = toy_signals()
            docs = s.assign(adsh=s["doc_id"], filename="x.htm")
            docs.to_csv(os.path.join(d, "edgar_docs.csv"), index=False)
            s[["cik", "date"]].to_csv(os.path.join(d, "filing_dates.csv"), index=False)
            hits = pd.DataFrame({"cik": [1, 2] * 12, "adsh": [f"a{i}" for i in range(24)],
                                 "file_date": [f"2024-{(i % 12) + 1:02d}-01" for i in range(24)],
                                 "sic": [7372, 6311] * 12, "kind": "ai"})
            hits.to_csv(os.path.join(d, "edgar_hits.csv"), index=False)
            pd.DataFrame({"cik": [1, 2, 3, 4], "sic": [5961, 7372, 6311, 3674],
                          "assets_base": [5e9, 1e9, 1e9, 1e9]}).to_csv(os.path.join(d, "firms.csv"), index=False)
            cfg = cli.Config(); cfg.data_dir = d; cfg.end_date = "2024-12-31"

            class A: source = "edgar"; min_text = 200; supplier_sic = "baseline"
            cli.cmd_build(cfg, A)
            ev = pd.read_csv(os.path.join(d, "events_edgar.csv")).set_index("cik")
            self.assertTrue(str(ev.loc[2, "exclusion"]).startswith("R4"))
            fm = pd.read_csv(os.path.join(d, "firm_month_edgar.csv"))
            self.assertEqual(set(fm["cik"]), {1})

    def test_build_edgar_counts_filings_not_documents(self):
        """A filing whose main document and exhibit both mention RAG counts once in S."""
        from aitx import cli
        with tempfile.TemporaryDirectory() as d:
            docs = pd.DataFrame({
                "cik": [1, 1, 1, 1], "adsh": ["f1", "f1", "f2", "f3"],
                "filename": ["main.htm", "ex99.htm", "main.htm", "main.htm"],
                "date": ["2024-01-10", "2024-01-10", "2024-03-10", "2024-06-10"],
                "rag": [True, True, True, False], "ft": [False, False, False, True], "ai": True})
            docs["doc_id"] = docs["adsh"] + ":" + docs["filename"]
            docs.to_csv(os.path.join(d, "edgar_docs.csv"), index=False)
            pd.DataFrame({"cik": 1, "date": ["2024-01-10", "2024-03-10", "2024-06-10"]}).to_csv(
                os.path.join(d, "filing_dates.csv"), index=False)
            pd.DataFrame({"cik": [1], "adsh": ["f1"], "file_date": ["2024-01-10"], "sic": [7372],
                          "kind": "ai"}).to_csv(os.path.join(d, "edgar_hits.csv"), index=False)
            pd.DataFrame({"cik": [1], "sic": [5961], "assets_base": [5e9]}).to_csv(
                os.path.join(d, "firms.csv"), index=False)
            cfg = cli.Config(); cfg.data_dir = d; cfg.end_date = "2024-12-31"

            class A: source = "edgar"; min_text = 200; supplier_sic = "baseline"
            cli.cmd_build(cfg, A)
            fm = pd.read_csv(os.path.join(d, "firm_month_edgar.csv"))
            self.assertLessEqual(fm["S_share"].max(), 1.0)
            self.assertEqual(fm.loc[fm["month"] == "2024-02", "cum_rag"].item(), 1)




class TestInventory(unittest.TestCase):
    def test_board_slug(self):
        self.assertEqual(cc.board_slug("https://boards.greenhouse.io/Acme/jobs/1?x=y"), "acme")
        self.assertEqual(cc.board_slug("https://jobs.lever.co/acme-corp/0f8c2d3e-aaaa-bbbb-cccc-000000000000"),
                         "acme-corp")
        self.assertEqual(cc.slug_candidates("Rocket Companies, Inc.", first_word=False),
                         ["rocketcompanies", "rocket-companies"])

    def test_inventory_keeps_detail_html_only(self):
        rows = [{"url": "https://boards.greenhouse.io/acme/jobs/123", "timestamp": "20240101000000",
                 "filename": "f", "offset": "0", "length": "9", "mime": "text/html"},
                {"url": "https://boards.greenhouse.io/acme", "timestamp": "20240101000000",
                 "filename": "f", "offset": "0", "length": "9", "mime": "text/html"}]
        orig = cc._cdx_query_files
        cc._cdx_query_files = lambda client, crawl, pat: rows if pat.startswith("boards.greenhouse") else []
        try:
            out = list(cc.inventory(None, "CC-MAIN-2024-10"))
        finally:
            cc._cdx_query_files = orig
        self.assertEqual([(r["ats"], r["slug"], r["crawl"]) for r in out], [("greenhouse", "acme", "CC-MAIN-2024-10")])

    def test_cc_match_rule(self):
        from aitx import cli
        with tempfile.TemporaryDirectory() as d:
            pd.DataFrame({"cik": [1, 2, 3], "ticker": ["AC", "AC2", "BE"],
                          "name": ["Acme Corp", "Acme, Inc.", "Beta Widgets Inc."]}).to_csv(
                os.path.join(d, "universe.csv"), index=False)
            pd.DataFrame({"ats": ["greenhouse", "lever", "lever"], "slug": ["acme", "betawidgets", "beta"],
                          "url": ["u1", "u2", "u3"]}).to_csv(os.path.join(d, "cc_inventory.csv"), index=False)
            cfg = cli.Config(); cfg.data_dir = d
            cli.cmd_cc_match(cfg, None)
            m = pd.read_csv(os.path.join(d, "ats_map.csv"))
            # 'acme' is claimed by two firms -> dropped; 'beta' (first word only) is not a candidate
            self.assertEqual(m[["cik", "ats", "slug"]].values.tolist(), [[3, "lever", "betawidgets"]])


if __name__ == "__main__":
    unittest.main()
