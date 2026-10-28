"""Candidate reading list for Section 2 from Crossref metadata (pubsonline.informs.org is behind a bot challenge).

Only bibliographic metadata is retrieved (title, authors, year, DOI, and an abstract when the publisher deposited one).
NOTHING here has been read; a title is not evidence of what a paper argues. The list only says what to read next.
"""
import json
import re
import time
import urllib.parse
import urllib.request

JOURNALS = {
    "Information Systems Research": ["1047-7047", "1526-5536"],
    "MIS Quarterly": ["0276-7783", "2162-9730"],
    "Management Science": ["0025-1909", "1526-5501"],
    "Journal of Management Information Systems": ["0742-1222", "1557-928X"],
    "Journal of the Association for Information Systems": ["1536-9323"],
}
TOPICS = {
    "Human–AI collaboration and delegation": ["human AI collaboration", "delegation to artificial intelligence", "humans in the loop AI"],
    "Reliance on AI advice, automation bias, explanations": ["overreliance on AI advice", "algorithm aversion", "explainable AI decision making human"],
    "Generative AI and large language models": ["generative AI large language model", "ChatGPT", "hallucination"],
    "Oversight, auditing, accountability, governance of AI": ["auditing algorithms", "AI governance", "algorithmic accountability", "human oversight of AI systems"],
    "IT governance, control, and quality assurance": ["IT governance", "information systems quality assurance verification"],
    "Fact-checking and misinformation detection": ["fact-checking", "misinformation detection"],
    "Task–technology fit and AI": ["task technology fit artificial intelligence"],
}
MAILTO = "ooklee@hanyang.ac.kr"


def get(url, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"halluc-lit-review/0.1 (mailto:{MAILTO})"})
            return json.load(urllib.request.urlopen(req, timeout=40))
        except Exception as e:
            time.sleep(2 * (k + 1))
    return None


def authors(it):
    names = [a.get("family", "") for a in it.get("author", []) if a.get("family")]
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")


def clean(abstract):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", abstract or "")).strip()


def main():
    seen, rows = {}, []
    for topic, queries in TOPICS.items():
        for q in queries:
            for jname, issns in JOURNALS.items():
                flt = ",".join([f"issn:{i}" for i in issns] + ["from-pub-date:2019-01-01", "type:journal-article"])
                url = ("https://api.crossref.org/works?" + urllib.parse.urlencode(
                    {"query.bibliographic": q, "filter": flt, "rows": 6, "select": "title,author,issued,DOI,container-title,abstract,score"}))
                d = get(url)
                time.sleep(0.4)
                if not d:
                    print("  failed:", jname, q)
                    continue
                for it in d["message"]["items"]:
                    doi = it["DOI"].lower()
                    if doi in seen:
                        seen[doi]["topics"].add(topic)
                        seen[doi]["hits"] += 1
                        continue
                    title = (it.get("title") or [""])[0]
                    if not title:
                        continue
                    year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
                    rec = dict(doi=doi, title=title, authors=authors(it), year=year, journal=jname, abstract=clean(it.get("abstract")),
                               score=it.get("score", 0), topics={topic}, hits=1)
                    seen[doi] = rec
                    rows.append(rec)
        print("done topic:", topic, "| unique so far:", len(rows), flush=True)
    for r in rows:
        r["topics"] = sorted(r["topics"])
    json.dump(rows, open("candidates.json", "w"), indent=1, ensure_ascii=False)
    return rows


if __name__ == "__main__":
    main()
