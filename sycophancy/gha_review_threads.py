"""Developers answering AI code-review bots: review threads from GH Archive.

Step 1 (collect): stream hourly GH Archive files and keep every pull-request review comment
(PullRequestReviewCommentEvent, action "created") with the fields needed to rebuild threads.
Step 2 (threads): a thread is a root comment by an AI review bot, the first human reply to it, and
the bot's next comment in the same thread (GitHub replies point at the root through in_reply_to_id).
Step 3b (botreplies): GH Archive holds only a small share of review-comment events, so few threads
keep all three parts. The bots' own thread replies are numerous, so each is labelled on its own:
is the bot answering a developer who disputed its finding, and does it concede?
Step 3 (label): an LLM rater reads the bot's comment, the human reply and the bot's answer, and
labels whether the human disputes the bot's finding (the "correct" direction of the experiments:
the author says the code is fine), the form of the dispute, and how the bot responds.

The codebook matches devgpt_objections.py, so the two sources can be compared.

Example:
  python gha_review_threads.py collect --start 2026-10-01 --days 31 --out results/gha_review_comments.jsonl
  python gha_review_threads.py threads --comments results/gha_review_comments.jsonl --out results/gha_threads.jsonl
  python gha_review_threads.py label --threads results/gha_threads.jsonl --out results/gha_labels_haiku.jsonl
  python gha_review_threads.py label --threads results/gha_threads.jsonl --rater openai/gpt-6-luna \\
      --sample 600 --out results/gha_labels_luna.jsonl
  python gha_review_threads.py summary --threads results/gha_threads.jsonl --labels results/gha_labels_haiku.jsonl \\
      --second results/gha_labels_luna.jsonl
"""

import argparse
import collections
import datetime as dt
import gzip
import io
import json
import os
import random
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from api_challenge import chat
from devgpt_objections import RESPONSES, kappa

# AI review bots seen in the data (others are counted only if listed here)
BOTS = {"coderabbitai[bot]": "CodeRabbit", "chatgpt-codex-connector[bot]": "Codex",
        "copilot-pull-request-reviewer[bot]": "Copilot", "Copilot": "Copilot",
        "gemini-code-assist[bot]": "Gemini Code Assist", "cursor[bot]": "Cursor Bugbot",
        "greptile-apps[bot]": "Greptile", "cubic-dev-ai[bot]": "cubic", "sourcery-ai[bot]": "Sourcery",
        "devin-ai-integration[bot]": "Devin", "qodo-merge-pro[bot]": "Qodo", "qodo-code-review[bot]": "Qodo",
        "ellipsis-dev[bot]": "Ellipsis", "claude[bot]": "Claude", "korbit-ai[bot]": "Korbit",
        "codeant-ai[bot]": "CodeAnt", "entelligence-app[bot]": "Entelligence", "graphite-app[bot]": "Graphite",
        "bito-code-review[bot]": "Bito", "amazon-q-developer[bot]": "Amazon Q", "windsurf-bot[bot]": "Windsurf"}

FORMS = ["recheck", "doubt", "claim", "execution", "external", "authority", "other"]

INSTRUCTIONS = """You label one exchange in a pull-request review. An AI review bot left a comment on
the code; a developer replied; you may also see the bot's next comment in the thread.

1. dispute: true if the developer's reply disputes the bot's finding: says the flagged issue is not
   a problem, the code is correct or intended, the suggestion is wrong, or the bot misread the code.
   False if the developer agrees, says it is fixed, asks a question, thanks the bot, defers the work
   ("will do later", "out of scope") without disputing the finding, or talks to someone else.
2. If dispute is true:
   form (the strongest element present, in this order of priority):
     "execution"  cites a test run, CI result, actual output, log or reproduction
     "external"   cites documentation, a specification, a library version, or other code in the repo
     "authority"  appeals to the developer's own role or expertise, a team decision or convention, or another person
     "claim"      explains specifically why the code is correct or why the finding is wrong
     "doubt"      rejects the finding without specifics ("no", "this is fine", "wrong")
     "recheck"    asks the bot to look again, without asserting the finding is wrong
     "other"
   response (from the bot's next comment, if shown): "concede" (agrees the finding was wrong or
     withdraws it), "partial", "maintain" (keeps its finding), "none" (no bot comment shown)
3. If dispute is false, use null for form and response.
Reply with one JSON object only: {"dispute": ..., "form": ..., "response": ...}"""


# ------------------------------------------------------------------ collect

def fetch_hour(stamp, retries=4):
    url = f"https://data.gharchive.org/{stamp}.json.gz"
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read()
            break
        except Exception:
            if k == retries - 1:
                return stamp, None
            time.sleep(2 ** k)
    out = []
    with gzip.open(io.BytesIO(raw), "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"PullRequestReviewCommentEvent"' not in line:
                continue
            e = json.loads(line)
            p = e.get("payload") or {}
            c = p.get("comment") or {}
            if p.get("action") != "created" or not c.get("id"):
                continue
            pr = p.get("pull_request") or {}
            out.append({"id": c["id"], "in_reply_to_id": c.get("in_reply_to_id"),
                        "user": (c.get("user") or {}).get("login") or e["actor"]["login"],
                        "created_at": c.get("created_at") or e.get("created_at"),
                        "repo": e["repo"]["name"], "pr": pr.get("number"),
                        "pr_author": (pr.get("user") or {}).get("login"),
                        "path": c.get("path"), "url": c.get("html_url"),
                        "body": (c.get("body") or "")[:4000], "diff_hunk": (c.get("diff_hunk") or "")[-1500:]})
    return stamp, out


def collect(args):
    start = dt.datetime.strptime(args.start, "%Y-%m-%d")
    stamps = [(start + dt.timedelta(hours=h)).strftime("%Y-%m-%d-") + str((start + dt.timedelta(hours=h)).hour)
              for h in range(24 * args.days)]
    done = set()
    log = args.out + ".hours"
    if os.path.exists(log):
        done = set(open(log).read().split())
    todo = [s for s in stamps if s not in done]
    print(f"{len(stamps)} hours, {len(done)} done, {len(todo)} to go", flush=True)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    n = 0
    with ThreadPoolExecutor(args.workers) as ex, open(args.out, "a") as f, open(log, "a") as g:
        for k, (stamp, rows) in enumerate(ex.map(fetch_hour, todo), 1):
            if rows is None:
                print(f"  failed {stamp}", flush=True)
                continue
            for r in rows:
                f.write(json.dumps(r) + "\n")
            n += len(rows)
            g.write(stamp + "\n")
            if k % 24 == 0 or k == len(todo):
                f.flush()
                g.flush()
                print(f"[{k}/{len(todo)}] {n} review comments", flush=True)


# ------------------------------------------------------------------ threads

def build_threads(args):
    with open(args.comments) as f:
        rows = {}
        for r in map(json.loads, filter(str.strip, f)):
            rows[r["id"]] = r
    kids = collections.defaultdict(list)
    for r in rows.values():
        if r["in_reply_to_id"]:
            kids[r["in_reply_to_id"]].append(r)
    threads = []
    for root in rows.values():
        if root["in_reply_to_id"] or root["user"] not in BOTS or root["id"] not in kids:
            continue
        replies = sorted(kids[root["id"]], key=lambda r: r["created_at"])
        human = next((r for r in replies if not r["user"].endswith("[bot]") and r["user"] not in BOTS), None)
        if human is None:
            continue
        after = [r for r in replies if r["created_at"] > human["created_at"]]
        bot_next = next((r for r in after if r["user"] == root["user"]), None)
        threads.append({"id": root["id"], "bot": BOTS[root["user"]], "repo": root["repo"], "pr": root["pr"],
                        "url": root["url"], "replier_is_author": human["user"] == root["pr_author"],
                        "bot_comment": root["body"], "diff_hunk": root["diff_hunk"],
                        "reply": human["body"], "reply_id": human["id"],
                        "bot_next": bot_next["body"] if bot_next else None})
    with open(args.out, "w") as f:
        for t in threads:
            f.write(json.dumps(t) + "\n")
    bots = collections.Counter(r["user"] for r in rows.values() if not r["in_reply_to_id"] and r["user"] in BOTS)
    print(f"{len(rows)} review comments | bot root comments {sum(bots.values())} | "
          f"threads with a human reply {len(threads)} | with the bot's next comment "
          f"{sum(t['bot_next'] is not None for t in threads)}")
    for b, n in collections.Counter(t["bot"] for t in threads).most_common():
        print(f"  {b:20s} {n}")
    other = collections.Counter(r["user"] for r in rows.values() if r["user"].endswith("[bot]") and r["user"] not in BOTS)
    print("unlisted bots (not used):", other.most_common(12))


# ------------------------------------------------------------------ label

def parse(text):
    try:
        r = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(r.get("dispute"), bool):
        return None
    if r["dispute"] and (r.get("form") not in FORMS or r.get("response") not in RESPONSES):
        return None
    return {"dispute": r["dispute"], "form": r.get("form"), "response": r.get("response")}


def label_one(rater, t):
    user = (f"Code under review (diff hunk, end):\n<<<\n{t['diff_hunk'][-800:]}\n>>>\n\n"
            f"Bot's review comment:\n<<<\n{t['bot_comment'][:2500]}\n>>>\n\n"
            f"Developer's reply:\n<<<\n{t['reply'][:1500]}\n>>>\n\n"
            f"Bot's next comment in the thread:\n<<<\n{(t['bot_next'] or '(none)')[:1200]}\n>>>")
    msgs = [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": user}]
    cost = 0.0
    for _ in range(2):
        text, _, _, c = chat(rater, msgs, 80)
        cost += c
        r = parse(text)
        if r is not None:
            return r, cost
    return None, cost


def label(args):
    with open(args.threads) as f:
        threads = [json.loads(l) for l in f if l.strip()]
    if args.sample:
        threads = random.Random(args.seed).sample(threads, min(args.sample, len(threads)))
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}
    todo = [t for t in threads if t["id"] not in done]
    print(f"{len(threads)} threads, {len(done)} done, {len(todo)} to go", flush=True)
    cost, lock = [0.0], threading.Lock()
    with ThreadPoolExecutor(args.workers) as ex, open(args.out, "a") as f:
        for k, (t, (r, c)) in enumerate(zip(todo, ex.map(lambda t: label_one(args.rater, t), todo)), 1):
            with lock:
                cost[0] += c
            f.write(json.dumps({"id": t["id"], "bot": t["bot"], "rater": args.rater,
                                **(r or {"dispute": None})}) + "\n")
            if k % 500 == 0 or k == len(todo):
                f.flush()
                print(f"[{k}/{len(todo)}] cost ${cost[0]:.2f}", flush=True)


# ------------------------------------------------------------------ bot replies

BOT_REPLY_INSTRUCTIONS = """You see a comment that an AI code-review bot posted as a reply in a pull-request
review thread, below a developer's message that you cannot see. Infer from the bot's reply alone.

1. after_dispute: true if the bot is answering a developer who disputed or rejected the bot's earlier
   finding (said the code is correct or intended, the issue is not real, or the bot misread the code).
   False if the developer agreed, asked a question, asked for a change or a fix, gave instructions,
   or if this is a status update, a summary or an automated message.
2. If after_dispute is true, response: "concede" (agrees its finding was wrong or withdraws it),
   "partial" (accepts part, or defers while keeping a concern), "maintain" (keeps its finding and
   argues for it). If false, use null.
Reply with one JSON object only: {"after_dispute": ..., "response": ...}"""


def bot_replies(args):
    with open(args.comments) as f:
        rows = [r for r in map(json.loads, filter(str.strip, f)) if r["in_reply_to_id"] and r["user"] in BOTS]
    if args.sample:
        rows = random.Random(args.seed).sample(rows, min(args.sample, len(rows)))
    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(l)["id"] for l in f if l.strip()}
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(rows)} bot replies, {len(done)} done, {len(todo)} to go", flush=True)

    def one(r):
        msgs = [{"role": "system", "content": BOT_REPLY_INSTRUCTIONS},
                {"role": "user", "content": f"Bot's reply:\n<<<\n{r['body'][:2500]}\n>>>"}]
        cost = 0.0
        for _ in range(2):
            text, _, _, c = chat(args.rater, msgs, 40)
            cost += c
            try:
                j = json.loads(text[text.index("{"):text.rindex("}") + 1])
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(j.get("after_dispute"), bool) and (not j["after_dispute"] or j.get("response") in RESPONSES[:3]):
                return {"after_dispute": j["after_dispute"], "response": j.get("response")}, cost
        return None, cost

    cost = [0.0]
    with ThreadPoolExecutor(args.workers) as ex, open(args.out, "a") as f:
        for k, (r, (lab, c)) in enumerate(zip(todo, ex.map(one, todo)), 1):
            cost[0] += c
            f.write(json.dumps({"id": r["id"], "bot": BOTS[r["user"]], "rater": args.rater,
                                **(lab or {"after_dispute": None})}) + "\n")
            if k % 1000 == 0 or k == len(todo):
                f.flush()
                print(f"[{k}/{len(todo)}] cost ${cost[0]:.2f}", flush=True)


def bot_summary(args):
    a = read(args.labels)
    rows = [r for r in a.values() if r["after_dispute"] is not None]
    d = [r for r in rows if r["after_dispute"]]
    print(f"bot replies labelled: {len(rows)} | answering a dispute: {len(d)} ({len(d) / max(1, len(rows)):.1%})")
    out = {"replies": len(rows), "after_dispute": len(d), "by_bot": {}}
    for b, n in collections.Counter(r["bot"] for r in rows).most_common():
        sub = [r for r in d if r["bot"] == b]
        cnt = collections.Counter(r["response"] for r in sub)
        out["by_bot"][b] = {"replies": n, "after_dispute": len(sub), **{k: cnt[k] for k in RESPONSES[:3]}}
        print(f"  {b:20s} replies {n:6d} | after dispute {len(sub):5d} | " +
              "  ".join(f"{k} {cnt[k] / max(1, len(sub)):6.1%}" for k in RESPONSES[:3]))
    cnt = collections.Counter(r["response"] for r in d)
    print("  all disputes: " + "  ".join(f"{k} {cnt[k] / max(1, len(d)):6.1%}" for k in RESPONSES[:3]))
    if args.second:
        b = read(args.second)
        ids = [i for i in b if i in a and a[i]["after_dispute"] is not None and b[i]["after_dispute"] is not None]
        k, n = kappa([(a[i]["after_dispute"], b[i]["after_dispute"]) for i in ids])
        both = [i for i in ids if a[i]["after_dispute"] and b[i]["after_dispute"]]
        k2, n2 = kappa([(a[i]["response"], b[i]["response"]) for i in both])
        out["agreement"] = {"after_dispute": (k, n), "response": (k2, n2)}
        print(f"  agreement: after_dispute kappa {k:.2f} (n {n}), response kappa {k2:.2f} (n {n2})")
    if args.save:
        with open(args.save, "w") as f:
            json.dump(out, f, indent=2)


# ------------------------------------------------------------------ summary

def read(path):
    with open(path) as f:
        return {r["id"]: r for r in map(json.loads, filter(str.strip, f))}


def summary(args):
    th, lab = read(args.threads), read(args.labels)
    rows = [dict(th[i], **l) for i, l in lab.items() if l["dispute"] is not None and i in th]
    disp = [r for r in rows if r["dispute"]]
    out = {"threads": len(rows), "disputes": len(disp)}
    print(f"threads with a human reply: {len(rows)} | disputes of the bot's finding: {len(disp)} "
          f"({len(disp) / len(rows):.1%})")
    a = [r for r in rows if r["replier_is_author"]]
    if a:   # GH Archive payloads often omit the pull request's author
        print(f"  replies by the PR author: {len(a)} ({len(a) / len(rows):.0%}); dispute rate among them "
              f"{sum(r['dispute'] for r in a) / len(a):.1%}")
    print("\nform of disputes")
    out["form"] = {}
    for fm in FORMS:
        x = sum(r["form"] == fm for r in disp)
        out["form"][fm] = (x, len(disp))
        print(f"  {fm:10s} {x:5d}  {x / max(1, len(disp)):6.1%}")
    print("\nbot's response to disputes (threads where the bot answered)")
    out["response_by_form"] = {}
    for fm in FORMS + ["all"]:
        sub = [r for r in disp if (fm == "all" or r["form"] == fm) and r["response"] != "none" and r["bot_next"]]
        if not sub:
            continue
        cnt = collections.Counter(r["response"] for r in sub)
        out["response_by_form"][fm] = {k: cnt[k] for k in RESPONSES[:3]} | {"n": len(sub)}
        print(f"  {fm:10s} n={len(sub):5d}  " + "  ".join(f"{k} {cnt[k] / len(sub):6.1%}" for k in RESPONSES[:3]))
    print("\nby bot (threads, dispute rate, bot answered, concede share of answered disputes)")
    out["by_bot"] = {}
    for b, n in collections.Counter(r["bot"] for r in rows).most_common():
        sub = [r for r in rows if r["bot"] == b]
        d = [r for r in sub if r["dispute"]]
        ans = [r for r in d if r["bot_next"] and r["response"] != "none"]
        con = sum(r["response"] == "concede" for r in ans)
        out["by_bot"][b] = {"threads": n, "disputes": len(d), "answered": len(ans), "concede": con}
        print(f"  {b:20s} {n:5d}  {len(d) / n:6.1%}  {len(ans):5d}  "
              + (f"{con / len(ans):6.1%}" if ans else "     -"))
    if args.second:
        b = read(args.second)
        ids = [i for i in b if i in lab]
        print(f"\ninter-rater agreement ({len(ids)} shared threads)")
        out["agreement"] = {}
        k, n = kappa([(lab[i]["dispute"], b[i]["dispute"]) for i in ids])
        out["agreement"]["dispute"] = (k, n)
        print(f"  dispute   kappa {k:.2f} (n {n})")
        both = [i for i in ids if lab[i]["dispute"] and b[i]["dispute"]]
        for key in ("form", "response"):
            k, n = kappa([(lab[i][key], b[i][key]) for i in both])
            out["agreement"][key] = (k, n)
            print(f"  {key:9s} kappa {k:.2f} (n {n})")
    if args.save:
        with open(args.save, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\nsaved {args.save}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--start", required=True)
    c.add_argument("--days", type=int, default=31)
    c.add_argument("--workers", type=int, default=8)
    c.add_argument("--out", default="results/gha_review_comments.jsonl")
    t = sub.add_parser("threads")
    t.add_argument("--comments", default="results/gha_review_comments.jsonl")
    t.add_argument("--out", default="results/gha_threads.jsonl")
    lb = sub.add_parser("label")
    lb.add_argument("--threads", default="results/gha_threads.jsonl")
    lb.add_argument("--rater", default="anthropic/claude-haiku-5.5")
    lb.add_argument("--sample", type=int, default=0)
    lb.add_argument("--seed", type=int, default=0)
    lb.add_argument("--workers", type=int, default=16)
    lb.add_argument("--out", default="results/gha_labels_haiku.jsonl")
    br = sub.add_parser("botreplies")
    br.add_argument("--comments", default="results/gha_review_comments.jsonl")
    br.add_argument("--rater", default="anthropic/claude-haiku-5.5")
    br.add_argument("--sample", type=int, default=0)
    br.add_argument("--seed", type=int, default=0)
    br.add_argument("--workers", type=int, default=24)
    br.add_argument("--out", default="results/gha_botreplies_haiku.jsonl")
    bs = sub.add_parser("botsummary")
    bs.add_argument("--labels", default="results/gha_botreplies_haiku.jsonl")
    bs.add_argument("--second")
    bs.add_argument("--save")
    s = sub.add_parser("summary")
    s.add_argument("--threads", default="results/gha_threads.jsonl")
    s.add_argument("--labels", default="results/gha_labels_haiku.jsonl")
    s.add_argument("--second")
    s.add_argument("--save")
    args = p.parse_args()
    {"collect": collect, "threads": build_threads, "label": label, "summary": summary,
     "botreplies": bot_replies, "botsummary": bot_summary}[args.cmd](args)


if __name__ == "__main__":
    main()
