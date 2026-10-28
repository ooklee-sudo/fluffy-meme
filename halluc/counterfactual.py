"""Counterfactual prefix experiment: does an earlier error raise the error rate of what follows?

For each entity whose 27B biography has a contradicted sentence, take the FIRST such sentence s*.
  corrupt arm : sentences[1..s*] unchanged (prefix ends with the erroneous sentence)
  clean arm   : same prefix, but sentence s* rewritten by the judge so it has no contradicted claim
The generator continues each prefix; the judge labels (prefix + continuation) with the same numbered-sentence
procedure as label_sent.py. Outcome = share of continuation sentences with a contradicted claim, paired by entity.
A third judge call marks continuation errors that merely restate / build on the prefix error ("dependent"), so the
effect can be split into repetition of the same error vs. new errors.
Caveat: the prefix is shown to the generator as text to continue, not as its own sampled tokens.
"""
import argparse
import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor

from common import DATA, chat, read_jsonl
from label_sent import PROMPT as JUDGE_PROMPT, parse, split_sentences

REWRITE = """REFERENCE (Wikipedia article on {title}):
\"\"\"
{ref}
\"\"\"

One sentence from a biography of {title} contains claims the reference contradicts:
SENTENCE: {sent}
CONTRADICTED CLAIMS:
{claims}

Rewrite the sentence so that none of those claims remain wrong: replace each with the correct fact if the reference states it, otherwise delete that claim. Keep the style and every other claim. Output only the rewritten sentence."""

CONTINUE = """Below is the beginning of a biography of {title}. Continue it with about {words} more words, in the same plain-prose style, picking up exactly where it stops. Do not repeat the beginning. Output only the continuation.

BEGINNING:
{prefix}"""

DEPEND = """An early sentence of a biography contained these WRONG claims:
{wrong}

Later in the text, the claims below were judged contradicted by the reference. List the numbers of those that merely repeat, restate, or logically depend on the early wrong claims (for example, a different date that only makes sense given the wrong birth year). Return ONLY a JSON array of numbers, [] if none.

LATER CONTRADICTED CLAIMS:
{later}"""


def judge(model, title, ref, sents):
    numbered = "\n".join(f"[{i}] {s}" for i, s in enumerate(sents, 1))
    p = JUDGE_PROMPT.format(title=title, ref=ref, sents=numbered)
    for _ in range(3):
        try:
            cl = parse(chat(model, p, 9000, 0.0), len(sents))
            if cl:
                return cl
        except Exception:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default=os.path.join(DATA, "gen_gemma-3-27b-it.jsonl"))
    ap.add_argument("--lab", default=os.path.join(DATA, "labs_gemma-3-27b-it.jsonl"))
    ap.add_argument("--entities", default=os.path.join(DATA, "entities.jsonl"))
    ap.add_argument("--generator", default="google/gemma-3-27b-it")
    ap.add_argument("--judge", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--max-sstar", type=int, default=8, help="only entities whose first error is within this sentence")
    ap.add_argument("--words", type=int, default=450)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(DATA, "cf_gemma-3-27b-it.jsonl"))
    a = ap.parse_args()

    ents = {e["title"]: e for e in read_jsonl(a.entities)}
    gens = {g["title"]: g for g in read_jsonl(a.gen)}
    pool = []
    for r in read_jsonl(a.lab):
        cs = sorted({c["sent"] for c in r["claims"] if c["label"] == "C"})
        if cs and cs[0] <= a.max_sstar and r["title"] in gens and r["title"] in ents:
            pool.append((r, cs[0]))
    random.Random(a.seed).shuffle(pool)
    done = {r["title"] for r in read_jsonl(a.out)}
    todo = [p for p in pool[: a.limit] if p[0]["title"] not in done]
    print(f"eligible {len(pool)}, running {len(todo)}", flush=True)
    lock = threading.Lock()

    def run(item):
        r, s_star = item
        t = r["title"]
        ref = ents[t]["reference"]
        sents = split_sentences(gens[t]["text"])
        if s_star > len(sents):
            return None
        bad = sents[s_star - 1]
        wrong = [c["claim"] for c in r["claims"] if c["sent"] == s_star and c["label"] == "C"]
        try:
            fixed = chat(a.judge, REWRITE.format(title=t, ref=ref, sent=bad, claims="\n".join("- " + w for w in wrong)), 400, 0.0).strip()
            arms = {}
            for arm, last in (("corrupt", bad), ("clean", fixed)):
                prefix = sents[: s_star - 1] + [last]
                cont = chat(a.generator, CONTINUE.format(title=t, words=a.words, prefix=" ".join(prefix)), 1200, 0.7).strip()
                allsents = prefix + split_sentences(cont)
                cl = judge(a.judge, t, ref, allsents)
                if cl is None:
                    return None
                arms[arm] = {"n_prefix": len(prefix), "n_sent": len(allsents), "claims": cl, "last_prefix_sentence": last}
            later = [c for c in arms["corrupt"]["claims"] if c["sent"] > s_star and c["label"] == "C"]
            dep = []
            if later:
                txt = chat(a.judge, DEPEND.format(wrong="\n".join("- " + w for w in wrong),
                                                 later="\n".join(f"{i}. {c['claim']}" for i, c in enumerate(later, 1))), 300, 0.0)
                try:
                    dep = [later[i - 1]["claim"] for i in json.loads(txt[txt.index("["): txt.rindex("]") + 1]) if 1 <= i <= len(later)]
                except Exception:
                    dep = []
            rec = {"title": t, "sitelinks": ents[t]["sitelinks"], "s_star": s_star, "wrong_claims": wrong, "bad_sentence": bad,
                   "fixed_sentence": fixed, "arms": arms, "dependent_claims": dep}
        except RuntimeError as err:
            print("  skip", t, str(err)[:80], flush=True)
            return None
        with lock:
            with open(a.out, "a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    with ThreadPoolExecutor(a.workers) as ex:
        new = [x for x in ex.map(run, todo) if x]
    print(f"{len(new)}/{len(todo)} done -> {a.out}")


if __name__ == "__main__":
    main()
