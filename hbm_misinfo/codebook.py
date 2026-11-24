"""HBM coding codebook (Layers A-C) as an LLM prompt plus a validator.

Mirrors "HBM Coding Codebook: Health Misinformation in Online Health
Communities (Draft v0.1)". If the codebook changes, change PROMPT and the
field lists here so that LLM output and human coding sheets stay aligned.
"""
from __future__ import annotations

CONSTRUCTS = ["B1", "B2", "B3", "B4", "B5", "B6"]
CONSTRUCT_NAMES = {
    "B1": "perceived susceptibility",
    "B2": "perceived severity",
    "B3": "perceived benefits",
    "B4": "perceived barriers",
    "B5": "cues to action",
    "B6": "self-efficacy",
}
CUES = ["C1", "C2", "C3", "C4", "C5", "C6"]
CLAIM_TYPES = ["treatment", "prevention", "cause", "diagnosis/symptom", "risk/side effect", "other"]
BEHAVIOR_CATS = ["adopt", "avoid", "delay", "discontinue", "substitute"]

SYSTEM = "You are a trained content-analysis coder. You follow the codebook exactly and reply with one JSON object only."

PROMPT = """Code the online health community message below with the HBM codebook.

LAYER A (screening)
- A1_health_claim: 1 if the message asserts something checkable about health causes, treatments, prevention, risks or outcomes; 0 for pure questions, emotional support or personal updates without an assertion. A question that presupposes a claim counts as that claim.
- Split the message into claims (one assertion about a cause, treatment, prevention, risk or outcome each). At most 3 claims; if more, keep the 3 most action-relevant and set more_claims = 1.
- Per claim: claim_text (one self-contained sentence that names the treatment or condition, so it can be fact-checked without the post. State the general health claim the message implies to the reader, not the anecdote: "I threw out my inhaler and use a breathing method, haven't needed it since" becomes "A breathing method can replace a prescribed asthma inhaler." If the message implies stopping, delaying or substituting a treatment, the claim must say so.); A2_claim_type (one of {claim_types}); A3_target_behavior (short phrase: the health action the claim pushes the reader toward); A3_category (one of {behavior_cats}); A4_recommended_care (what current medical guidance would recommend here, or "unclear"); A5_personal_experience (1 if backed by the author's own story).

LAYER B (per claim, six HBM constructs; judge from what the MESSAGE says or implies to the reader)
B1 perceived susceptibility: how likely the reader is to have/develop the condition or outcome.
B2 perceived severity: how serious the condition or its consequences are (magnified or minimized).
B3 perceived benefits: gains promised from a behavior. Also give object: "recommended_care" or "alternative" (whose benefits).
B4 perceived barriers: costs, risks, side effects, distrust or difficulty of a behavior. Also give object (whose barriers).
B5 cues to action: direct call to act now, deadline, testimony offered as a model, or a link/DM to buy. Generic "talk to your doctor" is not a cue.
B6 self-efficacy: reader's ability to manage alone/easily, or inability to cope with treatment.
For each construct give:
- pres: 0/1
- pushes: which behavior this element makes the reader MORE likely to choose: "recommended_care" (the A4 action), "alternative" (anything else, including doing nothing or the A3 behavior when it differs from A4), or "neither".
  Examples: "chemo poisons you" = B4 about recommended_care, pushes "alternative". "Fasting cured me" = B3 about alternative, pushes "alternative". "Stage 1 is basically nothing" = B2 minimized, pushes "alternative". "Don't stop it without your doctor" = pushes "recommended_care".
- int: 0 if absent; 1 passing mention; 2 argued or repeated; 3 central to the message, or stated with absolutes or loaded words ("poisons", "cure in 24 hours", "basically nothing", "you can absolutely do this").
Rules: code only what the author asserts (a quoted claim being refuted is coded as the refutation); hedging ("might not work for everyone", "check with your doctor") lowers int by one level but does not change pushes; ambiguous sarcasm -> literal meaning with pushes "neither".

LAYER C (once per message, each 0/1)
C1 claimed authority; C2 first-person testimony as proof; C3 fear/anger/hope as the main argument; C4 conspiracy or distrust of doctors/pharma/regulators; C5 social proof (numbers of people, upvotes); C6 offers a mechanism, data or checkable source.

Return JSON exactly in this shape:
{{"A1_health_claim": 0 or 1, "more_claims": 0 or 1,
 "claims": [{{"claim_id": "C1", "claim_text": "...", "A2_claim_type": "...", "A3_target_behavior": "...", "A3_category": "...",
   "A4_recommended_care": "...", "A5_personal_experience": 0,
   "B1": {{"pres": 0, "pushes": "neither", "int": 0}}, "B2": {{...}}, "B3": {{..., "object": "alternative"}}, "B4": {{..., "object": "recommended_care"}}, "B5": {{...}}, "B6": {{...}},
   "rationale": "one sentence"}}],
 "C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0, "C6": 0}}
If A1_health_claim is 0, return an empty claims list.

{context}MESSAGE:
\"\"\"{text}\"\"\"
"""


def build_prompt(text: str, parent_text: str | None = None) -> str:
    ctx = f'PARENT POST (context only, do not code):\n"""{parent_text}"""\n\n' if parent_text else ""
    return PROMPT.format(claim_types=", ".join(CLAIM_TYPES), behavior_cats=", ".join(BEHAVIOR_CATS),
                         context=ctx, text=text)


def _as_int(v, lo, hi, default=0):
    try:
        v = int(round(float(v)))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def validate(raw: dict) -> dict:
    """Coerce LLM output into the codebook's value ranges and enforce internal consistency."""
    out = {"A1_health_claim": _as_int(raw.get("A1_health_claim"), 0, 1),
           "more_claims": _as_int(raw.get("more_claims"), 0, 1), "claims": []}
    for c in CUES:
        out[c] = _as_int(raw.get(c), 0, 1)
    if out["A1_health_claim"] == 0:
        return out
    for k, cl in enumerate((raw.get("claims") or [])[:3]):
        rec = {
            "claim_id": f"C{k + 1}",
            "claim_text": str(cl.get("claim_text", "")),
            "A2_claim_type": cl.get("A2_claim_type") if cl.get("A2_claim_type") in CLAIM_TYPES else "other",
            "A3_target_behavior": str(cl.get("A3_target_behavior", "")),
            "A3_category": cl.get("A3_category") if cl.get("A3_category") in BEHAVIOR_CATS else "adopt",
            "A4_recommended_care": str(cl.get("A4_recommended_care", "unclear")),
            "A5_personal_experience": _as_int(cl.get("A5_personal_experience"), 0, 1),
            "rationale": str(cl.get("rationale", "")),
        }
        unclear = rec["A4_recommended_care"].strip().lower() in ("", "unclear")
        for b in CONSTRUCTS:
            v = cl.get(b) or {}
            pres = _as_int(v.get("pres"), 0, 1)
            # Direction is derived, not asked: the model only says which behavior is pushed.
            pushes = str(v.get("pushes", "neither")).strip().lower()
            d = {"recommended_care": 1, "alternative": -1}.get(pushes, 0) if pres and not unclear else 0
            i = _as_int(v.get("int"), 1, 3, default=1) if pres else 0
            item = {"pres": pres, "dir": d, "int": i}
            if b in ("B3", "B4"):
                obj = v.get("object")
                item["object"] = obj if pres and obj in ("recommended_care", "alternative") else ""
            rec[b] = item
        out["claims"].append(rec)
    if not out["claims"]:
        out["A1_health_claim"] = 0
    return out
