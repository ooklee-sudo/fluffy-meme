"""Rule-based extraction of the three stylistic event families (P, D, N).

Every event is returned as a token index, so any score can be traced back to
the exact tokens that produced it.
"""
from __future__ import annotations

import re

TOKEN_RE = re.compile(r"\w+(?:[-']\w+)*|[^\w\s]", re.UNICODE)

# Family P: academic punctuation and symbols
P_TOKENS = frozenset("()[];\"“”=<>±×%$∑∫≈≤≥")

# Family D: discourse markers (single- and multi-word, lowercase)
D_MARKERS = [
    "furthermore", "moreover", "therefore", "thus", "hence", "consequently",
    "however", "nevertheless", "nonetheless", "additionally", "crucially",
    "notably", "importantly", "specifically", "accordingly", "similarly",
    "in contrast", "in addition", "on the other hand", "by contrast",
    "as a result", "in particular", "for example", "for instance",
    "in conclusion", "in summary", "overall", "indeed",
]
_D_BY_LEN: dict[int, set[tuple[str, ...]]] = {}
for _m in D_MARKERS:
    _t = tuple(_m.split())
    _D_BY_LEN.setdefault(len(_t), set()).add(_t)

# Family N: passives and nominalizations
BE_FORMS = frozenset({"is", "are", "was", "were", "be", "been", "being"})
IRREGULAR_PP = frozenset(
    "shown given found made seen known taken written chosen built held "
    "done run set put read led begun drawn driven fallen grown kept "
    "left lost paid sent spent thought understood won".split()
)
ADVERBS_OK = re.compile(r"\w+ly$")
NOMINAL_SUFFIXES = ("tion", "sion", "ment", "ity", "ness")
NOMINAL_STOP = frozenset(
    "question section function mention station nation position condition "
    "environment government moment comment department city community "
    "university quality quantity activity ability security society "
    "business witness illness".split()
)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def _is_participle(w: str) -> bool:
    return w in IRREGULAR_PP or (len(w) > 4 and (w.endswith("ed") or w.endswith("en")))


def extract_events(tokens: list[str]) -> dict[str, list[int]]:
    """Return {family: [token indices]} for families 'P', 'D', 'N'."""
    low = [t.lower() for t in tokens]
    n = len(low)
    P = [i for i, t in enumerate(tokens) if len(t) == 1 and t in P_TOKENS]

    D: list[int] = []
    for i in range(n):
        for L, markers in _D_BY_LEN.items():
            if i + L <= n and tuple(low[i:i + L]) in markers:
                D.append(i)
                break

    N: list[int] = []
    for i, w in enumerate(low):
        if w in BE_FORMS:
            j = i + 1
            if j < n and ADVERBS_OK.match(low[j]):
                j += 1
            if j < n and _is_participle(low[j]):
                N.append(i)
                continue
        if (len(w) >= 7 and w.endswith(NOMINAL_SUFFIXES)
                and w not in NOMINAL_STOP and w.isalpha()):
            N.append(i)
    return {"P": P, "D": D, "N": sorted(set(N))}
