"""Phase 3 tasks whose demand for adapter capacity differs.

facts  Synthetic fact injection. N fictional people, each with one of 3 relations (department, home town,
       instrument) set to a fictional value drawn from 120 per relation, so the base model cannot know any
       of them. Each fact has 4 question templates: 2 for training, 1 for dev (early stopping) and 1 for
       evaluation, so evaluation asks every fact in wording not seen in training. Capacity demand grows
       with N: each fact carries about log2(120) = 7 bits.
math   MetaMathQA (GSM-derived rows) for training; GSM8K test questions for dev and evaluation, with the
       GSM8K solutions rewritten into MetaMathQA's style (calculator annotations removed, final line
       "The answer is: X").

Every example is (prompt text, response text); the loss and metrics are on the response only.
"""
import random
import re

SYL = ["ka", "lo", "ve", "ri", "tan", "mor", "esh", "ul", "pra", "zin", "dov", "qua", "bel", "sor", "nim", "teg",
       "ark", "fyl", "gon", "hes", "ix", "jor", "kel", "mav", "nor", "op", "ryn", "sev", "tor", "vex", "wyn", "yal"]

RELATIONS = {
    "department": (["Which department does {e} work in?", "{e} is employed in which department?",
                    "Name the department where {e} works.", "What is the department of {e}?"], "{v} Unit"),
    "town": (["Which town is {e} from?", "{e} grew up in which town?",
              "Name the home town of {e}.", "What is the home town of {e}?"], "{v}"),
    "instrument": (["Which instrument does {e} play?", "{e} plays which instrument?",
                    "Name the instrument that {e} plays.", "What instrument is played by {e}?"], "the {v}"),
}


def _word(rng, n_syl):
    return "".join(rng.choice(SYL) for _ in range(n_syl)).capitalize()


def make_facts(n, seed, n_values=120):
    """Return a list of facts: dict(entity, relation, value), all fictional and entity names unique."""
    rng = random.Random(seed)
    values = {}
    for rel in RELATIONS:
        vs = set()
        while len(vs) < n_values:
            vs.add(_word(rng, rng.choice([2, 3])))
        values[rel] = sorted(vs)
    names, facts = set(), []
    while len(facts) < n:
        e = f"{_word(rng, 2)} {_word(rng, 3)}"
        if e in names:
            continue
        names.add(e)
        rel = rng.choice(list(RELATIONS))
        facts.append(dict(entity=e, relation=rel, value=rng.choice(values[rel])))
    return facts


def fact_examples(facts, template_ids):
    out = []
    for f in facts:
        qs, ans = RELATIONS[f["relation"]]
        for t in template_ids:
            out.append((f"Q: {qs[t].format(e=f['entity'])}\nA:", " " + ans.format(v=f["value"])))
    return out


def facts_task(n, seed, n_dev=200, n_eval=1000):
    """(train, dev, eval) text pairs: train = templates 0 and 1 of all N facts; dev = template 2 of up to
    n_dev facts; eval = template 3 of up to n_eval facts (same facts, unseen wording)."""
    facts = make_facts(n, seed)
    rng = random.Random(seed + 1)
    train = fact_examples(facts, [0, 1])
    rng.shuffle(train)
    dev = fact_examples(rng.sample(facts, min(n_dev, n)), [2])
    ev = fact_examples(rng.sample(facts, min(n_eval, n)), [3])
    return train, dev, ev


def gsm8k_to_metamath(answer):
    body, final = answer.split("####")
    body = re.sub(r"<<[^>]*>>", "", body).strip()
    return f"{body}\nThe answer is: {final.strip()}"


def math_task(n_train, seed, n_dev=100, n_eval=500):
    from datasets import load_dataset

    mm = load_dataset("meta-math/MetaMathQA", split="train")
    mm = mm.filter(lambda r: r["type"].startswith("GSM"))
    idx = random.Random(seed).sample(range(len(mm)), n_train)
    train = [(f"Question: {mm[i]['query']}\nAnswer:", " " + mm[i]["response"]) for i in idx]
    gsm = load_dataset("openai/gsm8k", "main", split="test").shuffle(seed=seed)
    rows = [(f"Question: {r['question']}\nAnswer:", " " + gsm8k_to_metamath(r["answer"])) for r in gsm]
    return train, rows[:n_dev], rows[n_dev: n_dev + n_eval]


def encode(pairs, tok, max_len):
    out = []
    for p, r in pairs:
        pi = tok(p, add_special_tokens=True)["input_ids"][: max_len // 2]
        ri = tok(r + tok.eos_token, add_special_tokens=False)["input_ids"][: max_len - len(pi)]
        out.append((pi, ri))
    return out


if __name__ == "__main__":
    tr, dv, ev = facts_task(5, seed=0)
    for x in tr[:4] + ev[:2]:
        print(repr(x))
    print(gsm8k_to_metamath("Janet has 3 + 4 = <<3+4=7>>7 eggs.\n#### 7"))
