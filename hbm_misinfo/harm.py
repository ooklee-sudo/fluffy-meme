"""Codebook Section 6: harm-potential index and moderator priority tiers.

H_c = max(0, sum_k(-dir_k * int_k) / 18)   per claim; unit H = max over claims
P   = (C1 + C2 + C3 + C4 + C5) / 5          per unit (C6 reported separately)
Tiers combine Layer D veracity with H. The 0.33 cut-off is provisional.
"""
from __future__ import annotations

from codebook import CONSTRUCTS

H_CUTOFF = 0.33
FALSE_LIKE = {"refuted", "unsupported"}


def claim_harm(claim: dict) -> float:
    s = sum(-claim[b]["dir"] * claim[b]["int"] for b in CONSTRUCTS)
    return max(0.0, s / 18.0)


def persuasiveness(coded: dict) -> float:
    return sum(coded.get(c, 0) for c in ("C1", "C2", "C3", "C4", "C5")) / 5.0


def tier(veracity: str, h: float) -> int:
    if veracity in FALSE_LIKE and h >= H_CUTOFF:
        return 1
    if veracity in FALSE_LIKE or (veracity == "contested" and h >= H_CUTOFF):
        return 2
    return 3


TIER_NAMES = {1: "Urgent", 2: "Review", 3: "Monitor"}
