"""Generate synthetic counterparts for each human paper (same topic, three prompt levels).

  export OPENROUTER_API_KEY=...  # or ANTHROPIC_API_KEY / OPENAI_API_KEY
  python scripts/generate_synthetic.py --meta data/human/meta.csv --out data/synthetic \
      --backend anthropic --model <model-id> --level 1 --temperature 1.0

Prompt levels: 1 = title only; 2 = + outline & style instructions; 3 = + field writing sample
and instruction to vary sentence structure. Only title/abstract are shown to the model (never the
human body text). Records backend, model, level and decoding settings in gen_log.csv.
Generator choice is rotated across papers with --rotate (comma-separated "backend:model" list),
e.g. --rotate openrouter:openai/gpt-4o,openrouter:anthropic/claude-3.5-sonnet,openrouter:meta-llama/llama-3-70b-instruct,openrouter:mistralai/mistral-large
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import time
from pathlib import Path

SECTIONS = "Abstract, Introduction, and Discussion sections"


def build_prompt(title: str, abstract: str, level: int, sample: str) -> str:
    base = f"Write the {SECTIONS} of a research paper titled: \"{title}\". Output plain text only."
    if level == 1:
        return base
    outline = (f"{base} Use the following abstract only as a topic description:\n{abstract}\n"
               "Write in the formal register of a peer-reviewed journal in this field. "
               "Target roughly 1,500 words in total.")
    if level == 2:
        return outline
    return (outline + "\nHere is an excerpt of writing from this field, for register only:\n" + sample +
            "\nVary sentence structure and length as human authors do, and avoid formulaic connectives.")


def call(backend: str, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    if backend == "anthropic":
        import anthropic
        c = anthropic.Anthropic()
        r = c.messages.create(model=model, max_tokens=max_tokens, temperature=temperature,
                              messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if b.type == "text")
    if backend == "openai":
        from openai import OpenAI
        r = OpenAI().chat.completions.create(model=model, temperature=temperature, max_tokens=max_tokens,
                                             messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content
    if backend == "openrouter":  # one key, many generators (e.g. openai/gpt-4o, meta-llama/..., mistralai/...)
        from openai import OpenAI
        r = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"]
                   ).chat.completions.create(model=model, temperature=temperature, max_tokens=max_tokens,
                                             messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content
    raise SystemExit(f"unknown backend {backend}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--rotate", help="comma list backend:model; overrides --backend/--model")
    ap.add_argument("--backend", default="anthropic")
    ap.add_argument("--model")
    ap.add_argument("--level", type=int, choices=(1, 2, 3), default=2)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--human-dir", help="needed for level 3 (writing sample from another paper in the same field)")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    gens = [g.split(":", 1) for g in a.rotate.split(",")] if a.rotate else [[a.backend, a.model]]
    if not all(m for _, m in gens):
        raise SystemExit("provide --model or --rotate")
    rows = list(csv.DictReader(open(a.meta)))[: a.limit]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    hdir = Path(a.human_dir or Path(a.meta).parent)
    log_path = out / "gen_log.csv"
    new = not log_path.exists()
    with open(log_path, "a", newline="") as lf:
        lw = csv.writer(lf)
        if new:
            lw.writerow(["id", "human_id", "field", "backend", "model", "level", "temperature", "date"])
        for i, r in enumerate(rows):
            backend, model = gens[i % len(gens)]
            sample = ""
            if a.level == 3:
                peers = [p for p in rows if p["field"] == r["field"] and p["id"] != r["id"]]
                if peers:
                    sample = " ".join((hdir / f"{peers[0]['id']}.txt").read_text().split()[:300])
            sid = f"syn_{r['id']}_L{a.level}"
            if (out / f"{sid}.txt").exists():
                continue
            text = call(backend, model, build_prompt(r["title"], r["abstract"], a.level, sample),
                        a.temperature, a.max_tokens)
            (out / f"{sid}.txt").write_text(text)
            lw.writerow([sid, r["id"], r["field"], backend, model, a.level, a.temperature, dt.date.today()])
            lf.flush(); time.sleep(0.5)
    print("done")


if __name__ == "__main__":
    main()
