import re, numpy as np, pandas as pd, pyarrow.parquet as pq
D = "/tmp/aidev_v3"
pr = pd.read_parquet(f"{D}/pull_request.parquet", columns=["id", "agent", "user", "repo_url"]).rename(columns={"id": "pr_id", "user": "pr_user"})
CODE = {".py",".js",".ts",".tsx",".jsx",".java",".kt",".go",".rs",".c",".cc",".cpp",".h",".hpp",".cs",".rb",".php",".swift",".scala",".sh",".sql",".vue",".dart",".lua",".m",".r"}
SKIP = re.compile(r"(package-lock|yarn\.lock|pnpm-lock|\.lock$|\.min\.|\.snap$|/vendor/|/node_modules/|\.generated\.|_pb2|\.pb\.go|/dist/|/build/)", re.I)
STRICT = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
WIDE = re.compile(r"\b(todo|fixme|hack|xxx|workaround|temporary fix|for now)\b", re.I)
def ext(f):
    i = f.rfind("."); return f[i:].lower() if i >= 0 else ""
rows = []
pf = pq.ParquetFile(f"{D}/pr_commit_details.parquet")
for b in pf.iter_batches(batch_size=40000, columns=["pr_id", "sha", "author", "filename", "patch"]):
    for pid, sha, au, fn, patch in zip(*(b.column(c).to_pylist() for c in ("pr_id", "sha", "author", "filename", "patch"))):
        if not fn or not patch or ext(fn) not in CODE or SKIP.search(fn): continue
        added = [l[1:] for l in patch.split("\n") if l.startswith("+") and not l.startswith("+++")]
        if not added: continue
        txt = "\n".join(added)
        rows.append((pid, sha, au, len(added), len(STRICT.findall(txt)), len(WIDE.findall(txt))))
c = pd.DataFrame(rows, columns=["pr_id", "sha", "author", "added", "strict", "wide"])
c = c.merge(pr, on="pr_id", how="left")
c.to_parquet("/tmp/satd/commit_file_counts.parquet"); print("code file rows", len(c), "PRs", c.pr_id.nunique())
