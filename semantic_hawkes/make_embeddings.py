"""Cache (K, D) type-text embeddings for a TPP-LLM text dataset.

    python -m semantic_hawkes.make_embeddings --data semantic_hawkes/real_data/tppllm/stack-overflow \
        --encoder hf:Qwen/Qwen2.5-0.5B --out semantic_hawkes/emb/stack-overflow_qwen.npy
"""
import argparse
import json
import os

import numpy as np

from .encoders import encode


def type_texts(data_dir):
    """type id -> text, checked to be a bijection over the training split."""
    mp = {}
    for seq in json.load(open(os.path.join(data_dir, "train.json"))):
        for k, t in zip(seq["type_event"], seq["type_text"]):
            assert mp.setdefault(k, t) == t, f"type {k} has two texts: {mp[k]!r} / {t!r}"
    K = max(mp) + 1
    assert sorted(mp) == list(range(K)), "type ids are not contiguous"
    assert len(set(mp.values())) == K, "two type ids share the same text"
    return [mp[k] for k in range(K)]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--encoder", default="hash")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    texts = type_texts(a.data)
    emb = encode(texts, a.encoder)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.save(a.out, emb.astype(np.float32))
    print(a.out, emb.shape, texts[:5])
