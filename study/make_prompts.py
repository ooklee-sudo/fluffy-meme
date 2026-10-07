"""Create generation prompts: one synthetic-paper task per human paper (same topic)."""
import json, sys, random
rows = [json.loads(l) for l in open("data/human.jsonl", encoding="utf-8")]
levels = ["Write a research paper on the following topic.",
          "You are an experienced researcher. Write the full text of a journal-quality research paper (Introduction, Methods, Results, Discussion; no reference list) of about 3,000 words, with realistic citations in text and equations where appropriate.",
          "Write the full body of a scientific paper in the style of a top journal, about 3,000 words, with formal academic English, in-text citations, and quantitative results."]
rng = random.Random(7)
with open("data/prompts.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        lv = rng.randrange(3)
        f.write(json.dumps(dict(human_id=r["id"], field=r["field"], prompt_level=lv + 1,
            prompt=f"{levels[lv]}\n\nTitle: {r['title']}\n\nAbstract: {r['abstract']}")) + "\n")
print("prompts:", len(rows))
