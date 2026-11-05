"""Within-author comparison of AI-labeled vs. other commits.

Indicators per commit (source files only):
  add, dele      added / deleted lines
  satd           added lines containing TODO|FIXME|HACK|XXX
  elig, dup      non-trivial added lines, and those duplicated within the same commit
Usage: python mine.py <bare_repo_dir> <out.jsonl>
"""
import json, re, subprocess, sys
from collections import Counter

repo, out = sys.argv[1], sys.argv[2]
SINCE = "2025-04-01"
AI_RE = re.compile(
    r"co-authored-by:[^\n]*(claude|anthropic|copilot|cursor|codex|openai|devin|gemini|aider)"
    r"|generated with \[?claude code", re.I)
TOOL_RE = [("claude", re.compile(r"claude|anthropic", re.I)),
           ("codex", re.compile(r"codex|openai", re.I)),
           ("cursor", re.compile(r"cursor", re.I)),
           ("copilot", re.compile(r"copilot", re.I)),
           ("other", re.compile(r"devin|gemini|aider", re.I))]
BOT_RE = re.compile(r"\[bot\]|bot@|renovate|dependabot|github-actions|-bot\b|getsantry", re.I)
SRC_EXT = re.compile(r"\.(py|ts|tsx|js|jsx|mjs|go|rs|java|kt|rb|php|c|cc|cpp|h|hpp|cs|swift|scala|vue|svelte)$")
SKIP = re.compile(r"(^|/)(node_modules|vendor|dist|build|generated|__generated__|migrations|locales?|i18n|snapshots?|__snapshots__)/"
                  r"|\.min\.js$|\.d\.ts$|_pb2\.py$|\.pb\.go$|\.gen\.(go|ts)$|lock", re.I)
SATD = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
TRIVIAL = re.compile(r"^[\s\W]*$")

def git(*a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, errors="replace").stdout

shallow = set()
try:
    shallow = set(open(f"{repo}/shallow").read().split())
except FileNotFoundError:
    pass

meta = {}
for rec in git("log", "--no-merges", f"--since={SINCE}", "--format=%H%x00%ae%x00%an%x00%at%x00%B%x01").split("\x01"):
    rec = rec.strip("\n")
    if not rec:
        continue
    h, ae, an, at, body = rec.split("\x00", 4)
    if h in shallow or BOT_RE.search(ae) or BOT_RE.search(an):
        continue
    m = AI_RE.search(body)
    tool = None
    if m:
        for name, rx in TOOL_RE:
            if rx.search(m.group(0)):
                tool = name
                break
    meta[h] = dict(h=h, author=ae.lower(), ts=int(at), ai=bool(m), tool=tool)

proc = subprocess.Popen(["git", "-C", repo, "log", "--no-merges", f"--since={SINCE}", "--format=@@@C %H",
                         "-p", "--unified=0", "--no-color", "-M"],
                        stdout=subprocess.PIPE, text=True, errors="replace")
cur, f_ok, added = None, False, []
stats = {}

def flush():
    if cur is None or cur not in meta:
        return
    s = stats[cur]
    norm = [re.sub(r"\s+", " ", l.strip()) for l in added]
    elig = [l for l in norm if len(l) >= 25 and not TRIVIAL.match(l)
            and not l.startswith(("import ", "from ", "#include", "//", "#", "*", "/*"))]
    c = Counter(elig)
    s["elig"] = len(elig)
    s["dup"] = sum(v for v in c.values() if v >= 2)
    s["satd"] = sum(1 for l in added if SATD.search(l))

with open(out, "w") as fo:
    for line in proc.stdout:
        if line.startswith("@@@C "):
            flush()
            if cur in meta and stats[cur]["add"] + stats[cur]["dele"] > 0:
                fo.write(json.dumps({**meta[cur], **stats[cur]}) + "\n")
            cur = line.split()[1]
            stats[cur] = dict(add=0, dele=0, files=0)
            added, f_ok = [], False
        elif line.startswith("diff --git"):
            path = line.rstrip().split(" b/", 1)[-1]
            f_ok = bool(SRC_EXT.search(path)) and not SKIP.search(path)
            if f_ok:
                stats[cur]["files"] += 1
        elif not f_ok or line.startswith(("+++", "---")):
            continue
        elif line.startswith("+"):
            stats[cur]["add"] += 1
            added.append(line[1:])
        elif line.startswith("-"):
            stats[cur]["dele"] += 1
    flush()
    if cur in meta and stats[cur]["add"] + stats[cur]["dele"] > 0:
        fo.write(json.dumps({**meta[cur], **stats[cur]}) + "\n")
