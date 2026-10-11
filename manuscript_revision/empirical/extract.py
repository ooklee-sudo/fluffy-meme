import sys, json
# stdin: filtered GH Archive lines; stdout: compact jsonl of PR / review / review-comment events
def b(x, n): return (x or "")[:n]
for line in sys.stdin:
    try: e = json.loads(line)
    except Exception: continue
    t = e.get("type"); p = e.get("payload", {}); repo = e["repo"]["name"]
    if t == "PullRequestEvent":
        if p.get("action") != "closed": continue
        pr = p["pull_request"]; body = pr.get("body") or ""
        print(json.dumps(dict(k="pr", ev=e["created_at"], repo=repo, id=pr["id"], num=pr.get("number"),
            login=(pr.get("user") or {}).get("login"), utype=(pr.get("user") or {}).get("type"), ref=(pr.get("head") or {}).get("ref"),
            assoc=pr.get("author_association"), created=pr.get("created_at"), closed=pr.get("closed_at"),
            merged=pr.get("merged"), merged_at=pr.get("merged_at"), add=pr.get("additions"), dele=pr.get("deletions"),
            files=pr.get("changed_files"), commits=pr.get("commits"), comments=pr.get("comments"),
            rcomments=pr.get("review_comments"), draft=pr.get("draft"), title=b(pr.get("title"), 120),
            body_head=b(body, 300), body_len=len(body),
            claude=("Claude Code" in body) or ("claude.ai/code" in body),
            todo=sum(body.lower().count(w) for w in ("todo", "fixme", "hack", "workaround")),
            )))
    elif t == "PullRequestReviewEvent":
        pr = p["pull_request"]; r = p["review"]
        print(json.dumps(dict(k="rv", repo=repo, pid=pr["id"], pauthor=(pr.get("user") or {}).get("login"), who=(r.get("user") or {}).get("login"),
            wtype=(r.get("user") or {}).get("type"), state=r.get("state"), at=r.get("submitted_at"), blen=len(r.get("body") or ""))))
    elif t == "PullRequestReviewCommentEvent":
        pr = p["pull_request"]; c = p["comment"]
        print(json.dumps(dict(k="rc", repo=repo, pid=pr["id"], pauthor=(pr.get("user") or {}).get("login"), who=(c.get("user") or {}).get("login"),
            wtype=(c.get("user") or {}).get("type"), at=c.get("created_at"), blen=len(c.get("body") or ""))))
