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
    os.chmod(path, stat.S_IWRITE); func(path)


def process_repo(spec, models, out, tmp, today, max_mb=300):
    name = spec["full_name"] if isinstance(spec, dict) else spec
    if isinstance(spec, dict) and spec.get("size", 0) / 1024 > max_mb:
        print("  skip (large)", name); return
    url = name if os.path.exists(name) else f"https://github.com/{name}.git"
    dest = os.path.join(tmp, re.sub(r"[^\w.-]", "_", name))
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")            # do not download large-file pointers
    r = subprocess.run(["git", "-c", "core.longpaths=true", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.required=false", "-c", "core.protectNTFS=false",
                        "clone", "--quiet", "--no-tags", "--single-branch", url, dest], capture_output=True, text=True, timeout=1800, errors="ignore", env=env)
    if r.returncode != 0 and os.path.isdir(os.path.join(dest, ".git")):   # checkout of a few files failed (Windows paths) but the history is there
        r.returncode = 0
    if r.returncode != 0:
        print("  clone failed", name, r.stderr[:100].strip()); return
    try:
        for m, (a, s) in models.items():
            row = analyse_repo(dest, m, a, s, today)
            if row:
                row.update(repo=name, **({k: spec.get(k) for k in ("stargazers_count", "pushed_at", "language")} if isinstance(spec, dict) else {}))
                out.write(json.dumps(row) + "\n"); out.flush()
    finally:
        shutil.rmtree(dest, onerror=_rm)


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
        print("selftest ok", {k: ra[k] for k in ("lag_days", "flex_layer", "commit_files")}, {k: rb[k] for k in ("lag_days", "censored")})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--find-repos", action="store_true")
    ap.add_argument("--repos"); ap.add_argument("--out", default="results/history.jsonl"); ap.add_argument("--models", nargs="*")
    ap.add_argument("--default-set", action="store_true", help="use the retired text models of the OpenAI table")
    ap.add_argument("--max-repos", type=int, default=100000)
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    if a.find_repos: find_repos(a.out); sys.exit()
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
    with open(a.out, "a") as out, tempfile.TemporaryDirectory() as tmp:
        for i, sp in enumerate(specs, 1):
            if sp["full_name"] in done: continue
            print(f"[{i}/{len(specs)}] {sp['full_name']}", flush=True)
            try:
                process_repo(sp, models, out, tmp, dt.date.today())
                open(marker, "a").write(sp["full_name"] + "\n")
            except Exception as e:
                print("  failed", repr(e)[:120], flush=True)
