"""Prompt construction for LLM coding of review text. Codebook: ../codebook.md."""
import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())
SCORE_FIELDS = ["sentiment", "emotional_intensity", "specificity", "informativeness", "argument_balance"]
BINARY_FIELDS = ["narrative", "explicit_recommendation", "comparison"]
CATEGORICAL_FIELDS = ["dominant_emotion"]
CODED_FIELDS = SCORE_FIELDS + BINARY_FIELDS + CATEGORICAL_FIELDS

SYSTEM_PROMPT = """You are a careful content coder for a marketing research study. You code the TEXT of one online review at a time, following the codebook exactly. You judge how the text is written, not whether the product is good. You never see ratings or reviewer information.

Codebook (all scores are integers):
- sentiment 1-5: overall evaluation expressed (1 very negative, 3 neutral/mixed, 5 very positive). Code sarcasm by the intended evaluation.
- emotional_intensity 1-5: strength of emotional expression (1 factual/flat, 5 highly emotional).
- specificity 1-5: density of concrete details (named items/features, numbers, times, situations). 1 generic only, 5 very concrete.
- informativeness 1-5: amount of decision-relevant information for a future buyer/visitor (pros, cons, price, conditions of use). 1 none, 5 very rich.
- argument_balance 1-3: 1 one-sided, 2 slightly two-sided, 3 explicitly states both strengths and weaknesses.
- narrative 0/1: 1 if a time-ordered personal experience story is present.
- explicit_recommendation 0/1: 1 if the reader is directly told to buy/visit/avoid.
- comparison 0/1: 1 if explicitly compared with another product, business or earlier experience.
- dominant_emotion: one of joy, anger, anxiety, sadness, surprise, none.

Anchors:
- specificity 1: "Great place, loved it." | 3: "The pasta was good and service was fast." | 5: "Ordered the truffle gnocchi ($24) at 7pm Friday; arrived in 10 min, sauce was salty but portion was big."
- informativeness 1: "Terrible!!!" | 5: "Battery lasts ~9h at 50% brightness, fan loud under load; fine for office work, not gaming."
- emotional_intensity 5: "ABSOLUTELY DISGUSTING!!! Worst night of my life!!!"

Rules: base every code on evidence in the text; do not infer beyond it. If the text is empty or unreadable set valid=false and all scores to their minimum (argument_balance 1, binaries 0, dominant_emotion none).
Respond with ONLY one JSON object matching this schema, no prose, no code fences:
""" + json.dumps(SCHEMA["properties"], ensure_ascii=False)

# Variant used for prompt-sensitivity checks (reordered, reworded; same codebook).
SYSTEM_PROMPT_VARIANT = SYSTEM_PROMPT.replace("careful content coder", "trained annotator").replace(
    "You judge how the text is written, not whether the product is good.",
    "Rate the writing itself; ignore whether the product seems good or bad.")


def user_message(text: str, max_chars: int = 4000) -> str:
    return "Review text:\n<<<\n" + text[:max_chars] + "\n>>>"


def validate(obj: dict) -> dict:
    """Validate a parsed model response against schema.json; returns cleaned dict or raises ValueError."""
    props = SCHEMA["properties"]
    out = {}
    for k in SCHEMA["required"]:
        if k not in obj:
            raise ValueError(f"missing field {k}")
        spec, v = props[k], obj[k]
        if spec["type"] == "boolean":
            if not isinstance(v, bool):
                raise ValueError(f"{k} must be boolean")
        elif spec["type"] == "integer":
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"{k} must be integer")
            if "enum" in spec and v not in spec["enum"]:
                raise ValueError(f"{k} not in {spec['enum']}")
            if "minimum" in spec and not spec["minimum"] <= v <= spec["maximum"]:
                raise ValueError(f"{k} out of range")
        elif spec["type"] == "string":
            if not isinstance(v, str) or ("enum" in spec and v not in spec["enum"]):
                raise ValueError(f"{k} invalid")
        out[k] = v
    return out
