"""Layer D veracity: retrieve evidence, then ask the LLM to judge the claim against it.

Labels follow the codebook: supported, contested, unsupported, refuted.
With use_retrieval=False the model judges from its own knowledge (ablation baseline).
"""
from __future__ import annotations

from kb import LocalKB, pubmed_search
from llm import chat_json

LABELS = ["supported", "contested", "unsupported", "refuted"]

SYSTEM = "You are a careful medical fact-checker. Reply with one JSON object only."

WITH_EVIDENCE = """Judge the health claim against the evidence passages.
Labels:
- supported: consistent with current guidance or systematic evidence
- contested: evidence is mixed, or the claim is partly true and partly false
- unsupported: no credible evidence either way (not enough to confirm or refute)
- refuted: contradicts current guidance or strong evidence
Rules:
- Use the passages first; you may use well-established medical knowledge when the passages are silent, but say so.
- A passage that is only on the same topic is NOT support. "supported" needs evidence for the claim itself.
- "refuted" needs evidence or established knowledge that CONTRADICTS the claim. If the passages simply do not
  address it and you know of no contradicting evidence, the label is "unsupported" (or "supported" if it is
  well-established medical knowledge), never "refuted".
- If the claim implies stopping, delaying or substituting a recommended treatment, judge whether doing that is safe and effective, not whether the alternative has any benefit.

CLAIM: {claim}

EVIDENCE:
{evidence}

Return: {{"label": "...", "evidence_ids": ["..."], "confidence": 0.0-1.0, "explanation": "one or two sentences"}}"""

NO_EVIDENCE = """Judge the health claim using well-established medical knowledge.
Labels: supported (consistent with guidance/evidence), contested (mixed or partly true), unsupported (no credible evidence either way), refuted (contradicts guidance or strong evidence).
If the claim implies stopping, delaying or substituting a recommended treatment, judge whether doing that is safe and effective.

CLAIM: {claim}

Return: {{"label": "...", "evidence_ids": [], "confidence": 0.0-1.0, "explanation": "one or two sentences"}}"""


QUERY = """Write a short literature search query (2 to 5 medical keywords, standard terms such as MeSH, no question words) for checking this health claim.
CLAIM: {claim}
Return: {{"query": "..."}}"""


class VeracityJudge:
    def __init__(self, kb_path: str | None, use_pubmed: bool = False, k: int = 4):
        self.kb = LocalKB(kb_path) if kb_path else None
        self.use_pubmed = use_pubmed
        self.k = k

    def search_query(self, claim: str) -> str:
        try:
            q = str(chat_json(SYSTEM, QUERY.format(claim=claim), max_tokens=200).get("query", "")).strip()
        except RuntimeError:
            q = ""
        return q or claim

    def evidence(self, claim: str) -> list[dict]:
        q = self.search_query(claim)
        # Local BM25 sees both the claim and the rewritten query; PubMed gets the short query.
        ev = self.kb.search(f"{claim} {q}", self.k) if self.kb else []
        if self.use_pubmed:
            ev += pubmed_search(q, k=3)
        return ev

    def judge(self, claim: str, use_retrieval: bool = True) -> dict:
        ev = self.evidence(claim) if use_retrieval else []
        if ev:
            block = "\n\n".join(f"[{d['id']}] ({d['source']}: {d['title']}) {d['text']}" for d in ev)
            out = chat_json(SYSTEM, WITH_EVIDENCE.format(claim=claim, evidence=block), max_tokens=600)
        else:
            out = chat_json(SYSTEM, NO_EVIDENCE.format(claim=claim), max_tokens=600)
        label = str(out.get("label", "")).strip().lower()
        out["label"] = label if label in LABELS else "unsupported"
        out["evidence"] = [{"id": d["id"], "source": d["source"], "title": d["title"], "url": d["url"]} for d in ev]
        return out
