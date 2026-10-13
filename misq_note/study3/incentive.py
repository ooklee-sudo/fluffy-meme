"""Rule-based flag for reviews that disclose receiving the product free / discounted for a review (v3, fixed before analysis).
All conditions must hold within a single sentence."""
import re
_SPLIT = re.compile(r"[.!?\n]|<br\s*/?>", re.I)
_RECV = re.compile(r"\b(received|provided|given|gave|sent|offered|obtained|purchased|bought)\b", re.I)
_DISC = re.compile(r"\b(free|discount\w*|reduced|complimentary|promotion\w*|sample)\b", re.I)
_REV = re.compile(r"\b(review\w*|opinion|feedback|honest\w*|unbiased|evaluat\w*|test\w*)\b", re.I)
_EXCH = re.compile(r"(in (exchange|return) for|for)\s+(my|an|a|the|their)?\s*(honest|unbiased|fair|candid|personal|true)[^.]{0,25}\b(review|opinion|feedback|evaluation)", re.I)
_NEG = re.compile(r"\b(not|never|n't|no one|nobody)\b[^.]{0,25}\b(given|received|offered|provided)\b|\b(reviews?|reviewers|people)\b[^.]{0,30}\b(said|saw|read|say)\b", re.I)
def disclosed(text: str) -> bool:
    for s in _SPLIT.split(text or ""):
        if _NEG.search(s): continue
        if _EXCH.search(s) and (_DISC.search(s) or _RECV.search(s)): return True
        if _RECV.search(s) and _DISC.search(s) and _REV.search(s): return True
    return False
