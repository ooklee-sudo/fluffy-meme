"""Keyword dictionaries for RAG and fine-tuning (FT) signals.

Two layers:
1. SEARCH_PHRASES: exact phrases sent to EDGAR full-text search (high recall).
2. Regex rules with context checks, applied to the full document text
   (precision; removes e.g. 'RAG status' in project reports, 'fine-tune our
   strategy', and 'LoRaWAN').
"""
import re

# ---------------------------------------------------------------- search layer
SEARCH_PHRASES = {
    "rag": [
        "retrieval-augmented generation",
        "retrieval augmented generation",
        "RAG pipeline",
        "RAG architecture",
        "RAG-based",
        "vector database",
        "vector search",
        "embedding model",
        "RAG",                       # bare acronym; the regex layer drops 'RAG status' etc.
    ],
    "ft": [
        "fine-tuned model",
        "fine-tuned models",
        "fine-tuned large language model",
        "fine-tuning large language models",
        "fine-tune large language models",
        "parameter-efficient fine-tuning",
        "low-rank adaptation",
        "custom large language model",
        "proprietary large language model",
        "domain-specific large language model",
        "domain-specific language model",
        "reinforcement learning from human feedback",
        "train our own model",
        # broad terms: high recall, the regex layer requires AI-model context
        "fine-tuning",
        "fine-tuned",
        "fine-tune",
        "LoRA",
    ],
    # generic generative-AI activity, used for industry drift and volatility
    "ai": [
        "large language model",
        "generative AI",
    ],
}

# ---------------------------------------------------------------- regex layer
_F = re.IGNORECASE
AI_CONTEXT = re.compile(
    r"\b(LLMs?|large language models?|language models?|generative AI|gen ?AI|"
    r"foundation models?|GPT|Llama|embeddings?|retriev\w*|chatbots?|AI|"
    r"machine learning|neural|transformer)\b", _F)
# AI-model words; bare "model" is not enough ("fine-tune our business model")
FT_CONTEXT = re.compile(
    r"\b(LLMs?|(large )?language models?|foundation models?|(AI|ML|machine learning|deep learning|"
    r"generative|open[- ]weights?|open[- ]source|pre-?trained) models?|GPT|Llama|Mistral|"
    r"BERT|transformers?|neural networks?|generative AI|gen ?AI|artificial intelligence)\b", _F)

# 'LoRA' (capital A) is already AI-specific; only rule out stray acronym uses
LORA_CONTEXT = re.compile(r"\b(models?|adapters?|fine[- ]?tun\w*|LLMs?|weights|rank)\b", _F)

RAG_RULES = [
    ("rag_phrase", re.compile(r"\bretrieval[- ]augmented[- ]generation\b", _F), None),
    # bare 'RAG' must be upper case, not a Red-Amber-Green status, and near AI words
    ("rag_acronym", re.compile(r"\bRAG\b(?!\s*(status|rating|report|scale)\b)"), AI_CONTEXT),
    ("vector_db", re.compile(r"\bvector (database|store|search|index)(es|s)?\b", _F), AI_CONTEXT),
    ("embedding_pipeline", re.compile(r"\bembedding (model|pipeline)s?\b", _F), AI_CONTEXT),
]
RAG_EXCLUDE = re.compile(r"\bred[\s,/-]+amber[\s,/-]+green\b", _F)

FT_RULES = [
    ("fine_tune", re.compile(r"\bfine[- ]?tun(e|ed|es|ing)\b", _F), FT_CONTEXT),
    ("lora", re.compile(r"\bLoRA\b(?!WAN)"), LORA_CONTEXT),
    ("low_rank", re.compile(r"\blow[- ]rank adaptation\b", _F), None),
    ("peft", re.compile(r"\bPEFT\b|\bparameter[- ]efficient fine[- ]?tuning\b", _F), None),
    ("rlhf_dpo", re.compile(r"\bRLHF\b|\breinforcement learning from human feedback\b|"
                            r"\bdirect preference optimization\b", _F), None),
    ("custom_llm", re.compile(r"\b(proprietary|custom|custom[- ]trained|domain[- ]specific|in[- ]house)\s+"
                              r"(large\s+)?language models?\b", _F), None),
    ("own_model", re.compile(r"\btrain(ed|ing|s)?\s+(our|its|their)\s+own\s+"
                             r"(large language |foundation |AI |language )?models?\b", _F), None),
]

AI_RULES = [
    ("llm", re.compile(r"\blarge language models?\b|\bLLMs?\b", _F), None),
    ("genai", re.compile(r"\bgenerative (AI|artificial intelligence)\b", _F), None),
]

WINDOW = 150  # characters on each side for context checks and snippets


def _apply(rules, text, exclude=None):
    hits = []
    for name, pat, ctx in rules:
        for m in pat.finditer(text):
            lo, hi = max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)
            window = text[lo:hi]
            if exclude is not None and exclude.search(window):
                continue
            if ctx is not None:
                # context word must appear in the window other than the match itself
                around = text[lo:m.start()] + " " + text[m.end():hi]
                if not ctx.search(around):
                    continue
            hits.append((name, " ".join(window.split())))
    return hits


def classify(text):
    """Return dict with booleans rag/ft/ai, matched rule names and one snippet each."""
    text = text or ""
    rag = _apply(RAG_RULES, text, RAG_EXCLUDE)
    ft = _apply(FT_RULES, text)
    ai = _apply(AI_RULES, text)
    return {
        "rag": bool(rag), "ft": bool(ft), "ai": bool(ai) or bool(rag) or bool(ft),
        "rag_rules": ";".join(sorted({n for n, _ in rag})),
        "ft_rules": ";".join(sorted({n for n, _ in ft})),
        "rag_snippet": rag[0][1] if rag else "",
        "ft_snippet": ft[0][1] if ft else "",
    }
