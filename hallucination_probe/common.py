"""Shared helpers: data loading, model loading, prompt building, answer grading."""

import json
import re
import string
import unicodedata

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SYSTEM_PROMPT = "Answer the question with a short answer only (a few words). Do not explain."


# ---------------------------------------------------------------- data

def load_questions(name, n, seed=0, path=None):
    """Return a list of {"id", "question", "answers"} dicts.

    name: "triviaqa", "nq" (Natural Questions open), or "jsonl" (use --data-path;
    each line needs "question" and "answers" (list of strings); "id" is optional).
    """
    if name == "jsonl":
        rows = []
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if line.strip():
                    r = json.loads(line)
                    rows.append({"id": str(r.get("id", i)), "question": r["question"],
                                 "answers": list(r["answers"])})
        return rows[:n]

    from datasets import load_dataset

    if name == "triviaqa":
        ds = load_dataset("mandarjoshi/trivia_qa", "rc.nocontext", split="validation")
        ds = ds.shuffle(seed=seed).select(range(min(n, len(ds))))
        return [{"id": r["question_id"], "question": r["question"],
                 "answers": list(dict.fromkeys(r["answer"]["aliases"] + [r["answer"]["value"]]))}
                for r in ds]
    if name == "nq":
        ds = load_dataset("google-research-datasets/nq_open", split="validation")
        ds = ds.shuffle(seed=seed).select(range(min(n, len(ds))))
        return [{"id": str(i), "question": r["question"], "answers": list(r["answer"])}
                for i, r in enumerate(ds)]
    raise ValueError(f"unknown dataset: {name}")


# ---------------------------------------------------------------- model

def load_model(model_name, quant="4bit", adapter=None):
    """Load model + tokenizer. quant: "4bit", "8bit" or "none".

    adapter: optional path / hub id of a LoRA adapter (PEFT) applied on top of the model,
    e.g. to compare a model before and after fine-tuning.

    On a CPU (no CUDA) quantization is skipped, which is only meant for smoke tests
    with tiny models.
    """
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    if not torch.cuda.is_available():
        print("[warn] CUDA not found: loading on CPU in float32 without quantization.")
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32)
        return _with_adapter(model, adapter).eval(), tok

    kwargs = {"device_map": {"": 0}}  # keep everything on the GPU; never silently offload
    if quant in ("4bit", "8bit"):
        from transformers import BitsAndBytesConfig
        if quant == "4bit":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    else:
        kwargs["dtype"] = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(model_name, **kwargs)
    return _with_adapter(model, adapter).eval(), tok


def _with_adapter(model, adapter):
    if not adapter:
        return model
    from peft import PeftModel
    print(f"applying LoRA adapter: {adapter}")
    return PeftModel.from_pretrained(model, adapter)


# Few-shot plain-text prompt. Works the same way for base and instruct models, so two
# versions of a model can be compared on identical input text.
FEWSHOT = [
    ("What is the capital of France?", "Paris"),
    ("Who wrote the play Hamlet?", "William Shakespeare"),
    ("What is the chemical symbol for gold?", "Au"),
]


def build_prompt(tok, question, style="chat"):
    """style "chat": chat template (turns off Qwen3 'thinking' so answers stay short).
    style "fewshot": plain "Q: ... A:" prompt with three examples; the answer ends at
    the first newline."""
    if style == "fewshot":
        shots = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in FEWSHOT)
        return f"{SYSTEM_PROMPT}\n\n{shots}Q: {question}\nA:"
    if tok.chat_template:
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}]
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)
    return f"{SYSTEM_PROMPT}\n\nQ: {question}\nA:"


# ---------------------------------------------------------------- grading

def normalize(text):
    """SQuAD-style normalization (lowercase, strip punctuation/articles/spaces)."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = "".join(ch for ch in text if ch not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def grade(prediction, answers):
    """Return (exact_match, contains_match).

    contains_match = a gold alias appears inside the prediction. This is the usual
    automatic label for short-answer QA; check a sample by hand (or with an LLM judge
    in week 2) because it can be fooled by long or hedged answers.
    """
    pred = normalize(prediction)
    golds = [normalize(a) for a in answers if normalize(a)]
    em = any(pred == g for g in golds)
    contains = em or any(re.search(rf"(?<!\w){re.escape(g)}(?!\w)", pred) for g in golds)
    return em, bool(contains)
