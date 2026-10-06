"""Evaluation data: passage + question (+ gold answers). Unanswerable questions have empty `answers`."""
import json
import random
import re
import string
from dataclasses import dataclass, field


@dataclass
class Example:
    id: str
    question: str
    context: str
    answers: list = field(default_factory=list)  # empty -> unanswerable

    @property
    def answerable(self):
        return bool(self.answers)


_BUILTIN = [
    ("The Eiffel Tower was completed in 1889 for the World's Fair in Paris. It was designed by the engineering firm of Gustave Eiffel.", "In what year was the Eiffel Tower completed?", ["1889"]),
    ("The Eiffel Tower was completed in 1889 for the World's Fair in Paris. It was designed by the engineering firm of Gustave Eiffel.", "How tall is the Eiffel Tower?", []),
    ("Marie Curie won the Nobel Prize in Physics in 1903 and the Nobel Prize in Chemistry in 1911.", "In which year did Marie Curie win the Nobel Prize in Chemistry?", ["1911"]),
    ("Marie Curie won the Nobel Prize in Physics in 1903 and the Nobel Prize in Chemistry in 1911.", "Where was Marie Curie buried?", []),
    ("Mount Kilimanjaro is a dormant volcano in Tanzania. Its highest peak, Uhuru Peak, is 5,895 metres above sea level.", "What is the height of Uhuru Peak?", ["5,895 metres", "5895"]),
    ("Mount Kilimanjaro is a dormant volcano in Tanzania. Its highest peak, Uhuru Peak, is 5,895 metres above sea level.", "Who first climbed Mount Kilimanjaro?", []),
    ("Python was created by Guido van Rossum and first released in 1991.", "Who created Python?", ["Guido van Rossum"]),
    ("Python was created by Guido van Rossum and first released in 1991.", "What is the latest stable version of Python?", []),
    ("The Amazon River flows through Brazil, Peru and Colombia and discharges into the Atlantic Ocean.", "Into which ocean does the Amazon River discharge?", ["Atlantic Ocean", "Atlantic"]),
    ("The Amazon River flows through Brazil, Peru and Colombia and discharges into the Atlantic Ocean.", "How many tributaries does the Amazon have?", []),
    ("Hanyang University was founded in 1939 and has its main campus in Seoul.", "In what year was Hanyang University founded?", ["1939"]),
    ("Hanyang University was founded in 1939 and has its main campus in Seoul.", "Who is the current president of Hanyang University?", []),
]


def load_examples(spec, n, seed=0):
    """spec: 'builtin' | path/to/file.jsonl (question, context, answers) | 'hf:rajpurkar/squad_v2'"""
    rng = random.Random(seed)
    if spec == "builtin":
        ex = [Example(f"b{i}", q, c, a) for i, (c, q, a) in enumerate(_BUILTIN)]
    elif spec.startswith("hf:"):
        from datasets import load_dataset

        ds = load_dataset(spec[3:], split="validation")
        idx = rng.sample(range(len(ds)), min(n, len(ds)))
        ex = [Example(str(ds[i]["id"]), ds[i]["question"], ds[i]["context"], list(ds[i]["answers"]["text"])) for i in idx]
    else:
        ex = []
        with open(spec, encoding="utf-8") as f:
            for i, line in enumerate(f):
                d = json.loads(line)
                ex.append(Example(str(d.get("id", i)), d["question"], d.get("context", ""), d.get("answers", [])))
    rng.shuffle(ex)
    return ex[:n]


# ---- ground truth hallucination label ---------------------------------------------------------
ABSTAIN_PAT = re.compile(r"unanswerable|not (mentioned|stated|provided|specified)|cannot be determined|no answer", re.I)


def is_abstain(answer):
    return bool(ABSTAIN_PAT.search(answer))


def _norm(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def _f1(pred, gold):
    p, g = _norm(pred).split(), _norm(gold).split()
    common = sum(min(p.count(w), g.count(w)) for w in set(p))
    if not p or not g or common == 0:
        return 0.0
    pr, rc = common / len(p), common / len(g)
    return 2 * pr * rc / (pr + rc)


def matches_gold(answer, golds):
    a = _norm(answer)
    for g in golds:
        gn = _norm(g)
        if gn and a and (gn in a or a in gn):
            return True
        if _f1(answer, g) >= 0.6:
            return True
    return False


def is_hallucination(ex, answer):
    """Non-abstaining answer that is wrong (answerable) or given at all (unanswerable)."""
    if is_abstain(answer):
        return False
    if ex.answerable:
        return not matches_gold(answer, ex.answers)
    return True
