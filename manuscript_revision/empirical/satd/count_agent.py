import re, sys, pandas as pd, pyarrow.parquet as pq
sys.path.insert(0, "/tmp/satd"); from metrics import analyze
D = "/tmp/aidev_v3"
pr = pd.read_parquet(f"{D}/pull_request.parquet", columns=["id", "agent", "user", "repo_url"]).rename(columns={"id": "pr_id", "user": "pr_user"})
EXT = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript", ".java": "java", ".go": "go",
       ".rs": "rust", ".c": "c", ".h": "c", ".cc": "c++", ".cpp": "c++", ".hpp": "c++", ".php": "php", ".kt": "kotlin", ".swift": "swift",
       ".scala": "scala", ".rb": "ruby", ".sh": "shell"}
SKIP = re.compile(r"(package-lock|yarn\.lock|pnpm-lock|\.lock$|\.min\.|\.snap$|/vendor/|/node_modules/|\.generated\.|_pb2|\.pb\.go|/dist/|/build/)", re.I)
rows = []; pf = pq.ParquetFile(f"{D}/pr_commit_details.parquet")
for b in pf.iter_batches(batch_size=40000, columns=["pr_id", "sha", "author", "filename", "status", "patch"]):
    for pid, sha, au, fn, st, patch in zip(*(b.column(c).to_pylist() for c in ("pr_id", "sha", "author", "filename", "status", "patch"))):
        if not fn or not patch or SKIP.search(fn): continue
        i = fn.rfind("."); lang = EXT.get(fn[i:].lower()) if i >= 0 else None
        if not lang: continue
        added = [l[1:] for l in patch.split("\n") if l.startswith("+") and not l.startswith("+++")]
        m = analyze(added)
        if m: rows.append(dict(pr_id=pid, sha=sha, author=au, lang=lang, new_file=(st == "added"), **m))
c = pd.DataFrame(rows).merge(pr, on="pr_id", how="left"); c.to_parquet("/tmp/satd/agent_rows.parquet"); print("agent rows", len(c))
