"""Time-to-migration of repositories that used a retiring model identifier on the announcement date (no survivorship bias).
Unlike code search (which finds only files that STILL contain the identifier), this takes a repository frame that does not depend on the outcome,
clones each repository, and uses git history:
  at risk   = the repository tree on the announcement date contains the identifier (git grep at the last commit on or before that date)
  event     = the first commit after the announcement whose tree contains no occurrence of the identifier
  censored  = occurrences remain at HEAD (observed until today)
Per (repository, model) row: lag, censoring, occurrences at announcement and at HEAD, size of the migration commit (files, lines, prompt files),
flexibility proxies at announcement (provider-agnostic layer vs direct SDK, share of dated identifiers), and activity controls.
Run on your own machine; needs git on the PATH. Steps:
  python mine_by_history.py --find-repos --out results\\repos.jsonl         (needs GITHUB_TOKEN; builds the repository frame)
  python mine_by_history.py --repos results\\repos.jsonl --out results\\history.jsonl --models gpt-4-0314 gpt-3.5-turbo-0613 ...
  python mine_by_history.py --selftest
"""
import argparse, datetime as dt, json, os, re, shutil, stat, subprocess, sys, tempfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
LAYER = r"import litellm|from litellm|litellm\.completion|langchain_openai|from langchain|import langchain|from llama_index|import llama_index|portkey_ai|@ai-sdk/|from ai import|vercel/ai"
DIRECT = r"import openai|from openai|require\(.openai.\)|from .openai.|openai\.(ChatCompletion|chat)|OpenAI\("


def git(args, cwd, timeout=180, check=False):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout, errors="ignore")
    if check and r.returncode not in (0, 1):
        raise RuntimeError(f"git {' '.join(args[:3])} failed: {r.stderr[:200]}")
    return r


def grep_present(cwd, pattern, rev, fixed=True):
    return git(["grep", "-I", "-q"] + (["-F"] if fixed else ["-E", "-i"]) + ["-e", pattern, rev, "--"], cwd).returncode == 0


def grep_count(cwd, pattern, rev):
    r = git(["grep", "-I", "-c", "-F", "-e", pattern, rev, "--"], cwd)
    return sum(int(l.rsplit(":", 1)[1]) for l in r.stdout.splitlines() if ":" in l)


def analyse_repo(cwd, model, announced, shutdown, today):
    base = git(["rev-list", "-1", f"--before={announced.isoformat()}T23:59:59", "HEAD"], cwd).stdout.strip()
    if not base or not grep_present(cwd, model, base):
        return None
    row = dict(model=model, announced=str(announced), shutdown=str(shutdown), notice_days=(shutdown - announced).days, base_sha=base,
               occ_base=grep_count(cwd, model, base), occ_head=grep_count(cwd, model, "HEAD"))
    # flexibility proxies and controls at the announcement date
    row["flex_layer"] = grep_present(cwd, LAYER, base, fixed=False)
    row["direct_sdk"] = grep_present(cwd, DIRECT, base, fixed=False)
    since90 = (announced - dt.timedelta(days=90)).isoformat()
    log90 = git(["log", f"--since={since90}", f"--until={announced.isoformat()}T23:59:59", "--format=%ae", base], cwd).stdout.split()
    row["commits_prior90"] = len(log90); row["authors_prior90"] = len(set(log90))
    first = git(["log", "--reverse", "--format=%cI", "--max-parents=0", base], cwd).stdout.split()
    row["repo_age_days_at_announcement"] = (announced - dt.date.fromisoformat(first[0][:10])).days if first else None
    head_has = grep_present(cwd, model, "HEAD")
    event_sha = None
    if not head_has:
        cands = git(["log", f"--since={announced.isoformat()}T23:59:59", "--format=%H\t%cI", "--reverse", "-S" + model, "HEAD"], cwd, timeout=600).stdout.splitlines()
        for c in cands:
            sha, d = c.split("\t")
            if not grep_present(cwd, model, sha):
                event_sha, event_date = sha, dt.date.fromisoformat(d[:10]); break
        if event_sha is None:                                   # removed through a merge that -S does not show: fall back to HEAD
            event_sha = git(["rev-parse", "HEAD"], cwd).stdout.strip()
            event_date = dt.date.fromisoformat(git(["log", "-1", "--format=%cI", "HEAD"], cwd).stdout.strip()[:10]); row["event_at_head_fallback"] = True
    if event_sha:
        row.update(censored=False, lag_days=(event_date - announced).days, migration_sha=event_sha, migrated_before_shutdown=event_date <= shutdown)
        names = git(["show", "--name-only", "--format=", event_sha], cwd).stdout.split()
        stat_line = git(["show", "--shortstat", "--format=", event_sha], cwd).stdout
        ins = re.search(r"(\d+) insertion", stat_line); dele = re.search(r"(\d+) deletion", stat_line)
        row.update(commit_files=len(names), commit_additions=int(ins.group(1)) if ins else 0, commit_deletions=int(dele.group(1)) if dele else 0,
                   commit_touches_prompt=any("prompt" in n.lower() for n in names), commit_touches_tests=any("test" in n.lower() for n in names))
    else:
        row.update(censored=True, lag_days=(today - announced).days, migrated_before_shutdown=False)
    return row


def _rm(func, path, exc):
    try:
        os.chmod(path, stat.S_IWRITE); func(path)
    except OSError:
        pass


def rmtree_safe(path):
    """Delete a clone even when Windows paths exceed 260 characters or files are read-only; never raises."""
    if not os.path.exists(path):
        return
    p = os.path.abspath(path)
    if os.name == "nt":
        p = "\\\\?\\" + p if not p.startswith("\\\\?\\") else p        # extended-length path prefix
    shutil.rmtree(p, onerror=_rm)
    if os.path.exists(path) and os.name == "nt":                            # last resort
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", os.path.abspath(path)], capture_output=True)


def clone_repo(name, tmp):
    """Clone with Windows-safe options; returns the destination directory or None."""
    url = name if os.path.exists(name) else f"https://github.com/{name}.git"
    dest = os.path.join(tmp, re.sub(r"[^\w.-]", "_", name))
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")            # do not download large-file pointers
    r = subprocess.run(["git", "-c", "core.longpaths=true", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.required=false", "-c", "core.protectNTFS=false",
                        "clone", "--quiet", "--no-tags", "--single-branch", url, dest], capture_output=True, text=True, timeout=1800, errors="ignore", env=env)
    if r.returncode != 0 and os.path.isdir(os.path.join(dest, ".git")):   # checkout of a few files failed (Windows paths) but the history is there
        r.returncode = 0
    if r.returncode != 0:
        print("  clone failed", name, r.stderr[:100].strip()); return None
    return dest


def process_repo(spec, models, out, tmp, today, max_mb=300):
    name = spec["full_name"] if isinstance(spec, dict) else spec
    if isinstance(spec, dict) and spec.get("size", 0) / 1024 > max_mb:
        print("  skip (large)", name); return
    dest = clone_repo(name, tmp)
    if dest is None:
        return
    try:
        for m, (a, s) in models.items():
            row = analyse_repo(dest, m, a, s, today)
            if row:
                row.update(repo=name, **({k: spec.get(k) for k in ("stargazers_count", "pushed_at", "language", "frame")} if isinstance(spec, dict) else {}))
                out.write(json.dumps(row) + "\n"); out.flush()
    finally:
        rmtree_safe(dest)


# ---- second pass (--enrich): extra variables for the sensitivity analyses, computed for repositories already in history.jsonl ----
CONFIG_PATH = re.compile(r"(^|/)(\.env[^/]*|[^/]*\.(ya?ml|json|toml|ini|cfg|conf|properties|env)|[^/]*(config|settings)[^/]*)$", re.I)


def grep_counts_split(cwd, pattern, rev):
    """Occurrences of a fixed string at a revision, split into code files and configuration files (by path pattern)."""
    r = git(["grep", "-I", "-c", "-F", "-e", pattern, rev, "--"], cwd)
    code = cfg = 0
    for l in r.stdout.splitlines():
        if ":" not in l:
            continue
        path, n = l.split(":", 1)[1].rsplit(":", 1)
        if CONFIG_PATH.search(path): cfg += int(n)
        else: code += int(n)
    return code, cfg


def enrich_row(cwd, row, today):
    """Adds: externalised-model flag and 3-level flexibility at the announcement date; commits between the announcement and the end of the observation window
    (activity); and a relaxed migration date (identifier gone from code files, or total occurrences halved) alongside the strict one."""
    m, base = row["model"], row["base_sha"]
    ann, shut = dt.date.fromisoformat(row["announced"]), dt.date.fromisoformat(row["shutdown"])
    code0, cfg0 = grep_counts_split(cwd, m, base)
    out = dict(occ_code_base=code0, occ_cfg_base=cfg0, model_in_code=code0 > 0, model_in_config=cfg0 > 0)
    # ordinal flexibility: 0 hard-coded in source; 1 identifier only in configuration files; 2 provider-agnostic layer present
    out["flex_level"] = 2 if row.get("flex_layer") else (1 if code0 == 0 and cfg0 > 0 else 0)
    end = min(shut, today)
    n = git(["rev-list", "--count", f"--since={ann.isoformat()}T23:59:59", f"--until={end.isoformat()}T23:59:59", "HEAD"], cwd).stdout.strip()
    out["commits_to_shutdown"] = int(n) if n.isdigit() else None
    total0 = code0 + cfg0
    out.update(censored_relaxed=True, lag_relaxed=(today - ann).days)
    cands = git(["log", f"--since={ann.isoformat()}T23:59:59", "--format=%H\t%cI", "--reverse", "-S" + m, "HEAD"], cwd, timeout=600).stdout.splitlines()[:300]
    for c in cands:
        sha, d = c.split("\t"); code, cfg = grep_counts_split(cwd, m, sha)
        if code == 0 or (code + cfg) <= total0 / 2:
            out.update(censored_relaxed=False, lag_relaxed=(dt.date.fromisoformat(d[:10]) - ann).days); break
    return out


def enrich(history_path, out_path, today):
    rows = [json.loads(l) for l in open(history_path) if l.strip()]
    by_repo = {}
    for r in rows: by_repo.setdefault(r["repo"], []).append(r)
    marker = out_path + ".done"
    done = {l.strip() for l in open(marker)} if os.path.exists(marker) else set()
    with open(out_path, "a") as out, tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for i, (name, rs) in enumerate(by_repo.items(), 1):
            if name in done: continue
            print(f"[{i}/{len(by_repo)}] enrich {name}", flush=True)
            dest = clone_repo(name, tmp)
            if dest is None: continue
            try:
                for r in rs:
                    try: r.update(enrich_row(dest, r, today))
                    except Exception as e: print("  row failed", r["model"], repr(e)[:100]); continue
                    out.write(json.dumps(r) + "\n"); out.flush()
                open(marker, "a").write(name + "\n")
            finally:
                rmtree_safe(dest)


def find_repos(out_path, per_query=300, created_before="2025-06-01", pushed_after="2025-09-01"):
    sys.path.insert(0, HERE)
    from mine_migrations import gh
    import time
    # repositories that existed before the announcements (so they can be at risk) and are still active; not tied to any migration outcome
    queries = ["topic:openai", "topic:llm", "topic:chatgpt", "topic:langchain", "topic:gpt-4", "topic:gpt-3", "topic:ai-agents", "topic:chatbot", "topic:openai-api",
               "topic:generative-ai", "topic:rag", "topic:llm-agent", "topic:gpt", "topic:prompt-engineering", "topic:litellm", "topic:langchain-python"]
    seen = {}
    for q in queries:
        for page in range(1, per_query // 100 + 1):
            items = gh("/search/repositories", {"q": f"{q} created:<{created_before} pushed:>={pushed_after} stars:5..2000 fork:false archived:false", "per_page": 100, "page": page, "sort": "updated"}).get("items", [])
            for it in items:
                seen[it["full_name"]] = dict(full_name=it["full_name"], size=it["size"], stargazers_count=it["stargazers_count"], pushed_at=it["pushed_at"], language=it["language"])
            time.sleep(3)
            if len(items) < 100: break
    with open(out_path, "w") as f:
        for v in seen.values(): f.write(json.dumps(v) + "\n")
    print(len(seen), "repositories written to", out_path)


LAYER_TOPICS = ["litellm", "langchain", "langchain-python", "langchainjs", "llamaindex", "llama-index", "vercel-ai", "ai-sdk", "portkey", "openrouter",
                "llm-gateway", "llm-proxy", "multi-provider", "haystack", "semantic-kernel", "dspy", "instructor", "pydantic-ai", "crewai", "autogen"]
STAR_BANDS = ["5..20", "21..60", "61..200", "201..800", "801..3000"]


def find_repos_layer(out_path, exclude_path, per_query=300, created_before="2025-06-01", pushed_after="2025-09-01"):
    """Second frame aimed at provider-agnostic-layer users: topics of layer/framework libraries, split by star band so that each query stays under the
    1000-result search cap. Repositories already in the first frame are left out. Whether a repository really used a layer on the announcement date is still
    decided from its tree (flex_layer), not from the topic; the frame only raises the share of layer users. Rows carry frame='layer'."""
    sys.path.insert(0, HERE)
    from mine_migrations import gh
    import time
    have = set()
    for p in exclude_path or []:
        if os.path.exists(p): have |= {json.loads(l)["full_name"] for l in open(p) if l.strip()}
    seen = {}
    for q in LAYER_TOPICS:
        for band in STAR_BANDS:
            for page in range(1, per_query // 100 + 1):
                try:
                    items = gh("/search/repositories", {"q": f"topic:{q} created:<{created_before} pushed:>={pushed_after} stars:{band} fork:false archived:false", "per_page": 100, "page": page, "sort": "updated"}).get("items", [])
                except Exception as e:
                    print("  query failed", q, band, repr(e)[:80]); break
                for it in items:
                    if it["full_name"] not in have:
                        seen[it["full_name"]] = dict(full_name=it["full_name"], size=it["size"], stargazers_count=it["stargazers_count"], pushed_at=it["pushed_at"], language=it["language"], frame="layer")
                time.sleep(3)
                if len(items) < 100: break
        print(f"  {q}: {len(seen)} new repositories so far", flush=True)
    with open(out_path, "w") as f:
        for v in seen.values(): f.write(json.dumps(v) + "\n")
    print(len(seen), "repositories written to", out_path)


def selftest():
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_COMMITTER_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_EMAIL="t@x")
    def mk(base, name, commits):
        p = os.path.join(base, name); os.makedirs(p); subprocess.run(["git", "init", "-q", p], check=True)
        for date, files in commits:
            for fn, txt in files.items():
                os.makedirs(os.path.dirname(os.path.join(p, fn)) or p, exist_ok=True); open(os.path.join(p, fn), "w").write(txt)
            e = dict(env, GIT_AUTHOR_DATE=date + "T12:00:00", GIT_COMMITTER_DATE=date + "T12:00:00")
            subprocess.run(["git", "add", "-A"], cwd=p, check=True, env=e); subprocess.run(["git", "commit", "-q", "-m", "c", "--allow-empty"], cwd=p, check=True, env=e)
        return p
    with tempfile.TemporaryDirectory() as d:
        a = dt.date(2026, 4, 22); s = dt.date(2026, 10, 23)
        A = mk(d, "A", [("2026-03-01", {"app.py": "import litellm\nM='gpt-4-0613'\n"}), ("2026-06-01", {"app.py": "import litellm\nM='gpt-5'\n", "prompts/p.txt": "x\n"})])
        B = mk(d, "B", [("2026-03-01", {"app.py": "from openai import OpenAI\nM='gpt-4-0613'\n"}), ("2026-07-01", {"README.md": "hi\n"})])
        C = mk(d, "C", [("2026-03-01", {"app.py": "M='other'\n"})])
        D = mk(d, "D", [("2026-05-15", {"app.py": "M='gpt-4-0613'\n"})])
        ra, rb = analyse_repo(A, "gpt-4-0613", a, s, dt.date(2026, 10, 2)), analyse_repo(B, "gpt-4-0613", a, s, dt.date(2026, 10, 2))
        assert ra and not ra["censored"] and ra["lag_days"] == (dt.date(2026, 6, 1) - a).days and ra["flex_layer"] and not ra["direct_sdk"] and ra["commit_touches_prompt"], ra
        assert ra["migrated_before_shutdown"] and ra["occ_base"] == 1 and ra["occ_head"] == 0 and ra["commit_files"] == 2, ra
        assert rb and rb["censored"] and rb["direct_sdk"] and not rb["flex_layer"] and rb["occ_head"] == 1, rb
        assert analyse_repo(C, "gpt-4-0613", a, s, dt.date(2026, 10, 2)) is None            # not at risk: never contained the identifier
        assert analyse_repo(D, "gpt-4-0613", a, s, dt.date(2026, 10, 2)) is None            # created after the announcement: not at risk
        ea = enrich_row(A, ra, dt.date(2026, 10, 2)); eb = enrich_row(B, rb, dt.date(2026, 10, 2))
        assert ea["flex_level"] == 2 and not ea["censored_relaxed"] and ea["lag_relaxed"] == ra["lag_days"] and ea["commits_to_shutdown"] == 1, ea
        assert eb["flex_level"] == 0 and eb["censored_relaxed"] and eb["commits_to_shutdown"] == 1 and eb["model_in_code"], eb
        E = mk(d, "E", [("2026-03-01", {"app.py": "import openai\nM='gpt-4-0613'\n"}), ("2026-06-01", {"app.py": "import openai\nimport os\nM=os.environ['M']\n", ".env": "M=gpt-4-0613\n"})])
        re_ = analyse_repo(E, "gpt-4-0613", a, s, dt.date(2026, 10, 2)); ee = enrich_row(E, re_, dt.date(2026, 10, 2))
        assert re_["censored"] and not ee["censored_relaxed"] and ee["lag_relaxed"] == (dt.date(2026, 6, 1) - a).days, (re_, ee)   # strict: still present; relaxed: moved to config
        print("selftest ok", {k: ra[k] for k in ("lag_days", "flex_layer", "commit_files")}, {k: rb[k] for k in ("lag_days", "censored")})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--find-repos", action="store_true")
    ap.add_argument("--repos"); ap.add_argument("--out", default="results/history.jsonl"); ap.add_argument("--models", nargs="*")
    ap.add_argument("--default-set", action="store_true", help="use the retired text models of the OpenAI table")
    ap.add_argument("--max-repos", type=int, default=100000)
    ap.add_argument("--find-repos-layer", action="store_true", help="build the layer-targeted second frame (needs GITHUB_TOKEN); --exclude lists frames to leave out")
    ap.add_argument("--exclude", nargs="*"); ap.add_argument("--max-mb", type=int, default=300)
    ap.add_argument("--enrich", help="history.jsonl from a finished run: add flexibility level, activity and relaxed-migration variables (writes --out)")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    if a.find_repos: find_repos(a.out); sys.exit()
    if a.find_repos_layer: find_repos_layer(a.out, a.exclude); sys.exit()
    if a.enrich: enrich(a.enrich, a.out, dt.date.today()); sys.exit()
    o = pd.read_csv(os.path.join(HERE, "..", "data", "openai_deprecations.csv"), parse_dates=["announced", "shutdown"])
    names = a.models or []
    if a.default_set:
        bad = ("audio", "image", "tts", "realtime", "transcribe", "whisper", "dall-e", "sora", "moderation", "search", "computer-use", "codex", "api", "platform", "builder", "ft-")
        t = o[o.model.str.match(r"^(gpt-|o[134]|text-davinci|babbage|davinci)") & ~o.model.str.contains("|".join(bad)) & (o.shutdown < pd.Timestamp.today())]
        names = list(dict.fromkeys(t.model))
    models = {}
    for m in names:
        r = o[o.model == m].iloc[0]; models[m] = (r.announced.date(), r.shutdown.date())
    specs = [json.loads(l) for l in open(a.repos) if l.strip()][:a.max_repos]
    marker = a.out + ".done"
    done = {l.strip() for l in open(marker)} if os.path.exists(marker) else set()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "a") as out, tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for i, sp in enumerate(specs, 1):
            if sp["full_name"] in done: continue
            print(f"[{i}/{len(specs)}] {sp['full_name']}", flush=True)
            try:
                process_repo(sp, models, out, tmp, dt.date.today(), a.max_mb)
                open(marker, "a").write(sp["full_name"] + "\n")
            except Exception as e:
                print("  failed", repr(e)[:120], flush=True)
