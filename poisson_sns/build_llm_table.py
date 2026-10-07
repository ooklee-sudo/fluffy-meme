"""Build the LLM intensity-oracle lookup table over the 1,600 coarse states.

Each state is rated individually (own API call, Appendix A prompt), optionally
several times to measure repeatability. Resumable: finished states are cached.

  export ANTHROPIC_API_KEY=...      # set as an environment secret, never commit it
  python build_llm_table.py --model <model-id> --repeats 3 --out llm_table.json
  python build_llm_table.py --dry-run     # print a sample prompt, no API call
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from sim import all_states

PERSONA_TEXT = {
    "early_adopter": "an early adopter who enjoys trying new things first and posting about them",
    "cynic": "a cynic who is skeptical of trends and mostly reacts with critical comments",
    "trend_follower": "a trend follower who mostly reshares what others are already talking about",
    "lurker": "a lurker who reads much more than they write and rarely posts",
    "news_junkie": "a news junkie who follows current events closely and posts often",
}
PERIOD_TEXT = ["late night (0-6h)", "morning (6-12h)", "afternoon (12-18h)", "evening (18-24h)"]
REL_TEXT = ["low", "medium", "high"]

SYSTEM = ("You are the behavior controller of a virtual SNS user: {persona}. "
          "Given the user's current state and surroundings, rate on a real-valued scale from 0.0 to 5.0 "
          "the urge (Intensity) this user feels, within the next hour, to write a new post or leave a "
          "comment on the SNS.")


def user_prompt(key):
    p, pe, em, vb, rb, n = key
    if vb == 0:
        feed = "no posts on topics of interest appeared in the feed within the last hour."
    else:
        more = " or more" if vb == 3 else ""
        feed = (f"{vb}{more} posts on topics of interest appeared in the feed within the last hour "
                f"(the latest concerns a topic of {REL_TEXT[rb]} interest).")
    return (f"[Current situation] Time of day: {PERIOD_TEXT[p]}. Current emotion: {em}. "
            f"Timeline update: {feed} Notifications: {'present' if n else 'none'}.\n\n"
            '[Output format] Respond only in the following JSON format. {"intensity": '
            '(float between 0.0 and 5.0), "reason": "short reason"}')


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    v = float(json.loads(m.group(0))["intensity"])
    return min(5.0, max(0.0, v))


def rate(client, model, key, temperature):
    msg = client.messages.create(
        model=model, max_tokens=200, temperature=temperature,
        system=SYSTEM.format(persona=PERSONA_TEXT[key[1]]),
        messages=[{"role": "user", "content": user_prompt(key)}])
    return parse(msg.content[0].text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="llm_table.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    states = all_states()
    if a.dry_run:
        k = states[5]
        print(SYSTEM.format(persona=PERSONA_TEXT[k[1]]), "\n\n", user_prompt(k), sep="")
        print("\nstates:", len(states), " calls:", len(states) * a.repeats)
        return
    import anthropic
    client = anthropic.Anthropic()
    raw = json.load(open(a.out)) if os.path.exists(a.out) else {"model": a.model, "raw": {}}
    done = raw["raw"]

    def work(item):
        key, r = item
        for attempt in range(5):
            try:
                return key, r, rate(client, a.model, key, a.temperature)
            except Exception as e:  # rate limits, transient errors
                time.sleep(2 ** attempt)
        return key, r, None

    todo = [(k, r) for k in states for r in range(a.repeats)
            if len(done.get(json.dumps(k), [])) <= r]
    print("calls to make:", len(todo))
    with ThreadPoolExecutor(a.workers) as ex:
        for i, (key, r, v) in enumerate(ex.map(work, todo)):
            if v is not None:
                done.setdefault(json.dumps(key), []).append(v)
            if i % 200 == 0:
                json.dump({**raw, "raw": done}, open(a.out, "w"))
                print(i, "/", len(todo), flush=True)
    ratings = {k: sum(v) / len(v) for k, v in done.items() if v}
    json.dump({"model": a.model, "repeats": a.repeats, "temperature": a.temperature,
               "raw": done, "ratings": ratings}, open(a.out, "w"))
    print("states rated:", len(ratings), "of", len(states))


if __name__ == "__main__":
    main()
