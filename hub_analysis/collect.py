"""Collect adapter metadata from the Hugging Face Hub for several open-model lineages (public API, unauthenticated)."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

H = {"User-Agent": "research-probe"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hub_cache.json")

# family -> list of generations; each generation = list of repo ids (base and instruct variants)
FAM = {
    "Llama": [
        ["meta-llama/Llama-2-7b-hf", "meta-llama/Llama-2-7b-chat-hf", "meta-llama/Llama-2-13b-hf", "meta-llama/Llama-2-13b-chat-hf"],
        ["meta-llama/Meta-Llama-3-8B", "meta-llama/Meta-Llama-3-8B-Instruct", "meta-llama/Meta-Llama-3-70B", "meta-llama/Meta-Llama-3-70B-Instruct"],
        ["meta-llama/Llama-3.1-8B", "meta-llama/Llama-3.1-8B-Instruct", "meta-llama/Llama-3.1-70B", "meta-llama/Llama-3.1-70B-Instruct"],
        ["meta-llama/Llama-3.2-1B", "meta-llama/Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-3B", "meta-llama/Llama-3.2-3B-Instruct"],
    ],
    "Qwen": [
        ["Qwen/Qwen1.5-7B", "Qwen/Qwen1.5-7B-Chat", "Qwen/Qwen1.5-14B", "Qwen/Qwen1.5-1.8B"],
        ["Qwen/Qwen2-7B", "Qwen/Qwen2-7B-Instruct", "Qwen/Qwen2-1.5B", "Qwen/Qwen2-1.5B-Instruct", "Qwen/Qwen2-0.5B"],
        ["Qwen/Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen2.5-3B", "Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2.5-1.5B", "Qwen/Qwen2.5-1.5B-Instruct", "Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-14B", "Qwen/Qwen2.5-14B-Instruct"],
        ["Qwen/Qwen3-8B", "Qwen/Qwen3-8B-Base", "Qwen/Qwen3-4B", "Qwen/Qwen3-4B-Base", "Qwen/Qwen3-1.7B", "Qwen/Qwen3-0.6B", "Qwen/Qwen3-14B"],
    ],
    "Mistral": [
        ["mistralai/Mistral-7B-v0.1", "mistralai/Mistral-7B-Instruct-v0.1"],
        ["mistralai/Mistral-7B-Instruct-v0.2"],
        ["mistralai/Mistral-7B-v0.3", "mistralai/Mistral-7B-Instruct-v0.3"],
        ["mistralai/Mistral-Nemo-Base-2407", "mistralai/Mistral-Nemo-Instruct-2407"],
    ],
    "Gemma": [
        ["google/gemma-2b", "google/gemma-7b", "google/gemma-2b-it", "google/gemma-7b-it"],
        ["google/gemma-2-2b", "google/gemma-2-9b", "google/gemma-2-27b", "google/gemma-2-2b-it", "google/gemma-2-9b-it", "google/gemma-2-27b-it"],
        ["google/gemma-3-1b-pt", "google/gemma-3-4b-pt", "google/gemma-3-12b-pt", "google/gemma-3-1b-it", "google/gemma-3-4b-it", "google/gemma-3-12b-it"],
    ],
    "Phi": [
        ["microsoft/phi-1_5", "microsoft/phi-2"],
        ["microsoft/Phi-3-mini-4k-instruct", "microsoft/Phi-3-mini-128k-instruct", "microsoft/Phi-3-medium-4k-instruct"],
        ["microsoft/phi-4", "microsoft/Phi-4-mini-instruct"],
    ],
    "Yi": [
        ["01-ai/Yi-6B", "01-ai/Yi-6B-Chat", "01-ai/Yi-34B"],
        ["01-ai/Yi-1.5-6B", "01-ai/Yi-1.5-9B", "01-ai/Yi-1.5-6B-Chat", "01-ai/Yi-1.5-9B-Chat"],
    ],
    "InternLM": [
        ["internlm/internlm2-7b", "internlm/internlm2-chat-7b", "internlm/internlm2-base-7b"],
        ["internlm/internlm2_5-7b", "internlm/internlm2_5-7b-chat"],
        ["internlm/internlm3-8b-instruct"],
    ],
    "SmolLM": [
        ["HuggingFaceTB/SmolLM-135M", "HuggingFaceTB/SmolLM-360M", "HuggingFaceTB/SmolLM-1.7B", "HuggingFaceTB/SmolLM-135M-Instruct", "HuggingFaceTB/SmolLM-360M-Instruct", "HuggingFaceTB/SmolLM-1.7B-Instruct"],
        ["HuggingFaceTB/SmolLM2-135M", "HuggingFaceTB/SmolLM2-360M", "HuggingFaceTB/SmolLM2-1.7B", "HuggingFaceTB/SmolLM2-135M-Instruct", "HuggingFaceTB/SmolLM2-360M-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"],
    ],
    "Falcon": [
        ["tiiuae/falcon-7b", "tiiuae/falcon-7b-instruct", "tiiuae/falcon-40b"],
        ["tiiuae/Falcon3-7B-Base", "tiiuae/Falcon3-7B-Instruct", "tiiuae/Falcon3-1B-Base", "tiiuae/Falcon3-3B-Base", "tiiuae/Falcon3-10B-Base"],
    ],
    "DeepSeek": [
        ["deepseek-ai/deepseek-llm-7b-base", "deepseek-ai/deepseek-llm-7b-chat", "deepseek-ai/deepseek-coder-6.7b-base", "deepseek-ai/deepseek-coder-6.7b-instruct"],
        ["deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"],
    ],
}


def get(url):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), r.headers.get("Link")


def created(b):
    try:
        d, _ = get(f"https://huggingface.co/api/models/{b}")
        return d.get("createdAt")
    except Exception:
        return None


def adapters(b):
    url = f"https://huggingface.co/api/models?filter=base_model:adapter:{urllib.parse.quote(b, safe='/:')}&limit=1000&sort=createdAt&direction=1"
    out = []
    while url:
        d, link = get(url)
        for m in d:
            out.append([m.get("author") or m["id"].split("/")[0], m["createdAt"], m.get("downloads", 0) or 0, m.get("likes", 0) or 0, m["id"]])
        nx = re.search(r'<([^>]+)>;\s*rel="next"', link or "")
        url = nx.group(1) if nx else None
    return out


cache = json.load(open(OUT)) if os.path.exists(OUT) else {}
t0 = time.time()
for fam, gens in FAM.items():
    for gi, repos in enumerate(gens):
        for b in repos:
            if b in cache:
                continue
            c = created(b)
            ads = adapters(b) if c else []
            cache[b] = {"created": c, "adapters": ads}
            print(f"{fam} gen{gi} {b}: created={c} adapters={len(ads)} ({time.time()-t0:.0f}s)", flush=True)
            json.dump(cache, open(OUT, "w"))
json.dump({"FAM": FAM}, open(OUT.replace("hub_cache", "families"), "w"))
print("done", len(cache), "repos")
