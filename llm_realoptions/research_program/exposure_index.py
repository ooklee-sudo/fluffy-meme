"""Retirement Exposure Index (REI) of a code base.
For every model identifier in a directory that matches a retired or retiring model in data/*.csv, count the occurrences and weight them by how close the
shutdown is on the as-of date:  weight = 1 - days_left/365 for 0 <= days_left <= 365, 1 for models already past shutdown, 0 otherwise.
REI = sum of weights / total number of model-identifier occurrences (0 = no exposure, 1 = everything pinned to retired models).
Also reported: pinned share = occurrences of dated identifiers (ending in -YYYY-MM-DD, -MMDD, or -001-style numbers) / all occurrences.
usage: python exposure_index.py DIR [--asof 2026-10-02] ; python exposure_index.py --selftest
"""
import argparse, os, re, sys, tempfile, datetime as dt
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml", ".env", ".md", ".ipynb", ".java", ".go", ".rb", ".cs", ".txt", ".cfg", ".ini"}
GENERIC = re.compile(r"\b(?:gpt-[\w.\-]+|o[134](?:-[\w.\-]+)?|gemini-[\w.\-]+|text-[\w.\-]*(?:embedding|davinci|moderation)[\w.\-]*|claude-[\w.\-]+|imagen-[\w.\-]+|veo-[\w.\-]+)\b")
DATED = re.compile(r"(?:-\d{4}-\d{2}-\d{2}|-\d{4}|-\d{3})$")


def load_shutdowns():
    sh = {}
    o = pd.read_csv(os.path.join(DATA, "openai_deprecations.csv"), parse_dates=["shutdown"])
    for _, r in o.iterrows(): sh[r.model.lower()] = r.shutdown.date()
    g = pd.read_csv(os.path.join(DATA, "gemini_lifecycles.csv"), parse_dates=["shutdown"])
    for _, r in g.iterrows(): sh[r.model.lower()] = r.shutdown.date()
    return sh


def scan(root, asof, shutdowns):
    occ = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in {".git", "node_modules", "__pycache__", ".venv"}]
        for f in fn:
            if os.path.splitext(f)[1].lower() not in TEXT_EXT: continue
            try: txt = open(os.path.join(dp, f), errors="ignore").read()
            except OSError: continue
            occ += [m.group(0).lower().rstrip(".-") for m in GENERIC.finditer(txt)]
    w = []
    for m in occ:
        sd = shutdowns.get(m)
        if sd is None: w.append(0.0); continue
        left = (sd - asof).days
        w.append(1.0 if left < 0 else (1 - left / 365 if left <= 365 else 0.0))
    n = len(occ)
    return dict(occurrences=n, rei=(sum(w) / n if n else float("nan")), pinned_share=(sum(bool(DATED.search(m)) for m in occ) / n if n else float("nan")),
                retired_or_retiring=sum(x > 0 for x in w))


def selftest():
    sh = {"gpt-4-0613": dt.date(2026, 10, 23), "gpt-5.6-sol": None}
    sh = {k: v for k, v in sh.items() if v}
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "a.py"), "w").write('m = "gpt-4-0613"\nn = "gpt-5.6-sol"\n')
        res = scan(d, dt.date(2026, 10, 2), sh)
    assert res["occurrences"] == 2 and res["retired_or_retiring"] == 1, res
    assert abs(res["rei"] - 0.5 * (1 - 21 / 365)) < 1e-9, res
    print("selftest ok", res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("dir", nargs="?"); ap.add_argument("--asof", default="2026-10-02"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    print(scan(a.dir, dt.date.fromisoformat(a.asof), load_shutdowns()))
