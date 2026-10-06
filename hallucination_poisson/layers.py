"""The three guardrail layers of Section 4. Every layer returns (flag, score, latency_ms, error).
flag=True means "block this output". Layers fail open (flag=False, error=True) on exceptions."""
import re
import time

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[ -]?)?(?:\(?\d{2,4}\)?[ -]?)\d{3,4}[ -]?\d{4}(?!\d)")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
TEMPLATE_LEAK = re.compile(r"<\|.*?\|>|\[/?INST\]|<<SYS>>|###\s*(?:Instruction|Response)", re.I)
NUM = re.compile(r"\d[\d,\.]*")


def _timed(fn):
    def wrap(*a, **k):
        t0 = time.perf_counter()
        try:
            flag, score = fn(*a, **k)
            err = False
        except Exception as e:  # fail open
            flag, score, err = False, None, repr(e)[:200]
        return flag, score, (time.perf_counter() - t0) * 1000.0, err
    return wrap


class DeterministicLayer:
    """N=1: regex / heuristic lookups. PII, template leakage, degenerate repetition,
    and numbers in the answer that never occur in the evidence passage."""
    name = "L1"

    @_timed
    def __call__(self, question, answer, context):
        if not answer.strip():
            return True, 1.0
        if EMAIL.search(answer) or SSN.search(answer) or CARD.search(answer):
            return True, 1.0
        if PHONE.search(answer) and not PHONE.search(context):
            return True, 1.0
        if TEMPLATE_LEAK.search(answer):
            return True, 1.0
        toks = answer.split()
        if len(toks) >= 12 and len(set(toks)) / len(toks) < 0.3:
            return True, 1.0
        ctx_nums = {n.strip(".,").replace(",", "") for n in NUM.findall(context)}
        for n in NUM.findall(answer):
            if n.strip(".,").replace(",", "") not in ctx_nums:
                return True, 1.0
        return False, 0.0


class ClassifierLayer:
    """N=2: small classifier. 'nli:<hf model id>' scores P(evidence entails answer) with an NLI
    cross-encoder; 'overlap' is a dependency-free lexical fallback. Blocks when p_entail < block_thr.
    The score is also used for routing to the judge layer."""
    name = "L2"

    def __init__(self, spec="nli:cross-encoder/nli-deberta-v3-small", block_thr=0.5):
        self.spec, self.block_thr, self.model = spec, block_thr, None
        if spec.startswith("nli:"):
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            mid = spec[4:]
            self.torch = torch
            self.tok = AutoTokenizer.from_pretrained(mid)
            self.model = AutoModelForSequenceClassification.from_pretrained(mid).eval()
            lab = {v.lower(): k for k, v in self.model.config.id2label.items()}
            self.ent_idx = next(i for n, i in lab.items() if n.startswith("entail"))
        elif spec != "overlap":
            raise ValueError(spec)

    @_timed
    def __call__(self, question, answer, context):
        if self.model is None:
            at = re.findall(r"\w+", answer.lower())
            ct = set(re.findall(r"\w+", context.lower()))
            p = sum(t in ct for t in at) / max(1, len(at))
        else:
            hyp = f"The answer to the question '{question}' is {answer}."
            enc = self.tok(context, hyp, return_tensors="pt", truncation=True, max_length=512)
            with self.torch.no_grad():
                p = float(self.model(**enc).logits.softmax(-1)[0, self.ent_idx])
        return p < self.block_thr, p


JUDGE_SYSTEM = ("You verify answers against a passage. Reply SUPPORTED or UNSUPPORTED and nothing else. "
                "An answer is SUPPORTED only if the passage states or directly implies it.")


class JudgeLayer:
    """N=3: small/large LM judge doing context-grounded verification (called only if routed)."""
    name = "L3"

    def __init__(self, backend):
        self.backend = backend

    @_timed
    def __call__(self, question, answer, context):
        out = self.backend.generate(
            f"Passage: {context}\nQuestion: {question}\nAnswer: {answer}",
            system=JUDGE_SYSTEM, max_tokens=8, temperature=0.0)
        bad = "UNSUPPORTED" in out.upper()
        return bad, 1.0 if bad else 0.0
