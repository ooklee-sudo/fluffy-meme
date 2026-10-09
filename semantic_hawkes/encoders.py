"""Text encoders for event-type descriptions.

Event-type embeddings are computed once and cached (K is small), so even a
large LLM encoder adds no per-step cost during TPP training.
"""
import hashlib

import numpy as np


def hash_bow(descs, dim=64):
    """Dependency-free signed hashed bag-of-words (CPU smoke tests / baselines)."""
    out = np.zeros((len(descs), dim), dtype=np.float32)
    for r, d in enumerate(descs):
        for w in d.lower().split():
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            out[r, h % dim] += 1.0 if (h >> 20) & 1 else -1.0
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-8)


def hf_mean_pool(descs, model_name, device="cpu"):
    """Mean-pooled last hidden states of any HuggingFace encoder / decoder LLM."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModel.from_pretrained(model_name).to(device).eval()
    with torch.no_grad():
        batch = tok(descs, return_tensors="pt", padding=True).to(device)
        h = model(**batch).last_hidden_state
        m = batch["attention_mask"].unsqueeze(-1).to(h.dtype)
        emb = (h * m).sum(1) / m.sum(1)
    emb = emb.float().cpu().numpy()
    return emb / np.maximum(np.linalg.norm(emb, axis=1, keepdims=True), 1e-8)


def encode(descs, encoder="hash"):
    if encoder == "hash":
        return hash_bow(descs)
    if encoder.startswith("hf:"):
        return hf_mean_pool(descs, encoder[3:])
    raise ValueError(f"unknown encoder {encoder!r} (use 'hash' or 'hf:<model>')")
