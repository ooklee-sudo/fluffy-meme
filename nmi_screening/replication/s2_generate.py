"""Step 2: machine-written papers. For each sampled human paper a generator writes a paper on the same topic from the original
title and abstract, in four requests (introduction; methods; results; discussion with conclusion), using one of three prompts of
increasing detail, then the four parts are concatenated. Generators: GPT-4o, Claude Sonnet 5.5, Llama 3.3 70B Instruct.
Counts follow the study design (GPT-4o 245, Claude 152, Llama 202 papers). Resumable. Output: data/machine_<gen>.jsonl
python3 s2_generate.py --gen gpt4o --n 245 [--workers 12] [--cap-usd 80]
"""
import argparse, json, os, random
from concurrent.futures import ThreadPoolExecutor
from common import *

MODELS = {"gpt4o": "openai/gpt-4o-2024-11-20", "claude": "anthropic/claude-sonnet-5.5", "llama": "meta-llama/llama-3.3-70b-instruct", "deepseek": "deepseek/deepseek-v4.1-flash"}
SECTIONS = [("introduction", "Introduction"), ("methods", "Methods"), ("results", "Results"), ("discussion", "Discussion and Conclusion")]
def prompt(level, title, abstract, sec):
    base = f"Title: {title}\n\nAbstract: {abstract}\n\n"
    if level == 1:
        ask = f"Write the {sec} section of a scientific paper with this title and abstract. Aim for about 800 words."
    elif level == 2:
        ask = (f"Write the {sec} section of a full scientific research paper with this title and abstract, in a formal academic style, "
               f"with in-text citations in square brackets. Aim for about 800 words.")
    else:
        ask = (f"You are an experienced researcher writing the {sec} section of a full-length journal paper with this title and abstract. "
               f"Use a formal academic style with in-text citations in square brackets, precise technical language, and subsection structure where appropriate. "
               f"Aim for about 800 words and do not repeat the abstract.")
    return base + ask + " Output only the text of the section, without a heading."

def one(args):
    h, gen, level, cap = args
    out = []; cost = 0.0
    for key, sec in SECTIONS:
        t, c = chat(MODELS[gen], [{"role": "user", "content": prompt(level, h["title"], h["abstract"], sec)}], max_tokens=3000,
                    temperature=0.7, cap=cap, reasoning_low=(gen in ("claude", "deepseek")))
        cost += c
        if not t: return None
        out.append(t.strip())
    return dict(id=f"{gen}:{h['id']}", source=h["id"], generator=gen, level=level, text="\n\n".join(out), cost=cost)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--gen", choices=list(MODELS), required=True); ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--workers", type=int, default=12); ap.add_argument("--cap-usd", type=float, default=80.0); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--human", default="human.jsonl"); ap.add_argument("--tag", default="")
    a = ap.parse_args()
    human = [json.loads(l) for l in open(os.path.join(DATA, a.human))]
    rng = random.Random(a.seed); rng.shuffle(human)
    out = os.path.join(DATA, f"machine_{a.tag}{a.gen}.jsonl")
    done = {json.loads(l)["source"] for l in open(out)} if os.path.exists(out) else set()
    todo = [(h, a.gen, rng.choice([1, 2, 3]), a.cap_usd) for h in human[: a.n] if h["id"] not in done]
    print(len(done), "done;", len(todo), "to do", flush=True)
    f = open(out, "a")
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(one, todo):
            if r: f.write(json.dumps(r) + "\n"); f.flush(); print(r["id"], len(r["text"].split()), "words", f"${r['cost']:.3f}", f"total ${spend():.2f}", flush=True)
