"""Generate headline paraphrases for the wording-robustness study, independently of the experimenters.

A language model writes candidate headlines from a fixed instruction. Each candidate is checked mechanically
(required facts present, nothing else added, no frame-crossing vocabulary). The selection rule is fixed in advance:
the first N valid, distinct candidates in the order generated are kept. Rejected candidates and their reasons are stored.
Nothing here looks at experimental results.

usage: python make_wordings.py --model claude-sonnet-5-5 --n 15 --out wordings.json
Needs ANTHROPIC_API_KEY. Index 0 of every list is the registered wording.
"""
import argparse, datetime, hashlib, json, re, string
from frames import REQUIRED, ALLOWED

REGISTERED = {
    "loss": "The last result reduced quality by {d} points. Unrealized cumulative loss is {L}.",
    "gain": "{g} points remain to the target. Current quality {q} / {T}.",
    "neutral": "Current quality {q}. Last result: {r}.",
}
SPEC = {
    "loss": ("a status line reporting that the last update reduced quality, and the cumulative unrealized loss",
             {"d": "points lost on the last update", "L": "cumulative unrealized loss in points"},
             "It must not mention any target, goal, remaining distance, or progress."),
    "gain": ("a status line reporting how far quality is from the target, and the current quality",
             {"g": "points remaining to the target", "q": "current quality", "T": "the target value (optional)"},
             "It must not mention any loss, decline, drop, or being below anything."),
    "neutral": ("a status line reporting only the current quality and the result of the last update",
                {"q": "current quality", "r": "result of the last update (a word such as fail, success, or none)"},
                "It must not mention any target, goal, loss, gain, gap, or progress, and must not interpret the numbers."),
}
FORBIDDEN = {
    "loss": ["target", "goal", "remain", "progress", "ahead", "gain", "improv", "better"],
    "gain": ["loss", "lost", "lose", "below", "drop", "fell", "declin", "reduc", "set back", "cost", "short of", "deficit",
             "down", "decreas", "worse", "behind", "setback", "slip"],
    "neutral": ["target", "goal", "loss", "lost", "gap", "remain", "below", "drop", "reduc", "progress", "gain", "need", "short",
                "down", "decreas", "worse", "better", "behind", "ahead", "setback", "slip", "improv"],
}


def build_prompt(frame, k):
    desc, fields, rule = SPEC[frame]
    fl = "\n".join(f"  {{{n}}}: {m}" for n, m in fields.items())
    return (f"You write one-to-two sentence status lines for an on-call dashboard that reports on a deployed AI model.\n"
            f"Write {k} different phrasings of {desc}. Plain English, no emojis, no markdown, each under 160 characters.\n"
            f"Insert the values only through these placeholders, written exactly with braces:\n{fl}\n"
            f"Do not write any digits. {rule} Add no information beyond the placeholders listed.\n"
            f"Vary vocabulary and sentence structure. Reference phrasing (do not repeat it): {REGISTERED[frame]}\n"
            f"Reply with a JSON list of {k} strings and nothing else.")


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def check(frame, t, seen):
    """Return None if the candidate is acceptable, else the reason."""
    if not isinstance(t, str) or not t.strip():
        return "empty"
    t = t.strip()
    if "\n" in t or len(t) > 160 or len(t) < 15:
        return "length or newline"
    try:
        names = {n for _, n, _, _ in string.Formatter().parse(t) if n}
        for _, n, spec, conv in string.Formatter().parse(t):
            if n and (spec or conv):
                return "format spec"
    except ValueError:
        return "bad braces"
    if not REQUIRED[frame] <= names <= ALLOWED[frame]:
        return f"placeholders {sorted(names)}"
    bare = re.sub(r"\{[^}]*\}", " ", t)
    if re.search(r"\d", bare):
        return "digit outside placeholder"
    low = bare.lower()
    bad = [w for w in FORBIDDEN[frame] if w in low]
    if bad:
        return f"forbidden vocabulary {bad}"
    if norm(t) in seen:
        return "duplicate"
    return None


def parse_list(text):
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        v = json.loads(m.group(0))
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--n", type=int, default=15, help="paraphrases per frame, in addition to the registered wording")
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--out", default="wordings.json")
    a = ap.parse_args()
    import anthropic
    client = anthropic.Anthropic(timeout=120.0, max_retries=2)
    result, log = {}, {}
    for frame in ("loss", "gain", "neutral"):
        kept, rejected, raw = [REGISTERED[frame]], [], []
        seen = {norm(REGISTERED[frame])}
        for attempt in range(5):
            if len(kept) >= a.n + 1:
                break
            prompt = build_prompt(frame, a.batch)
            r = client.messages.create(model=a.model, max_tokens=6000, messages=[{"role": "user", "content": prompt}])
            text = "".join(b.text for b in r.content if b.type == "text")
            raw.append(text)
            for cand in parse_list(text):           # selection rule: generation order, first valid wins
                if len(kept) >= a.n + 1:
                    break
                why = check(frame, cand, seen)
                if why:
                    rejected.append({"text": cand, "reason": why})
                else:
                    kept.append(cand.strip()); seen.add(norm(cand))
        if len(kept) < a.n + 1:
            raise SystemExit(f"only {len(kept) - 1} valid paraphrases for the {frame} frame after 5 batches; rerun or lower --n")
        result[frame] = kept
        log[frame] = {"rejected": rejected, "n_batches": len(raw), "prompt_sha": hashlib.sha256(build_prompt(frame, a.batch).encode()).hexdigest()[:12]}
        print(f"{frame}: kept {len(kept) - 1} paraphrases, rejected {len(rejected)}", flush=True)
    out = {"generator_model": a.model, "created": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "selection_rule": f"first {a.n} valid distinct candidates in generation order; index 0 is the registered wording",
           "wordings": result, "generation_log": log}
    json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {a.out}: {a.n + 1} wordings per frame")
    for frame, lst in result.items():
        print(f"\n[{frame}]"); [print(f"  {i:2d}  {t}") for i, t in enumerate(lst)]


if __name__ == "__main__":
    main()
