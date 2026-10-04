"""LLM quality-requirement coding (0 low, 1 medium, 2 high) of the O*NET tasks scored >=1 for visual content creation."""
import json, os, sys, concurrent.futures as cf
import classify_onet as C
C.PROMPT=open("prompt_quality.txt").read()
key=os.environ["OPENROUTER_API_KEY"]; model="anthropic/claude-sonnet-5.5"; out="data/quality_sonnet55.jsonl"
tasks={t["id"]:t for t in C.load()}
cre=[json.loads(l) for l in open("data/all_creation_sonnet55.jsonl")]; cre=[x for x in cre if x["s"]>=1]
done=set()
if os.path.exists(out): done={json.loads(l)["id"] for l in open(out)}
todo=[x for x in cre if x["id"] not in done]; print("tasks to code:",len(todo),file=sys.stderr)
bs=[todo[i:i+20] for i in range(0,len(todo),20)]
with open(out,"a") as f, cf.ThreadPoolExecutor(3) as ex:
    futs={ex.submit(C.call,model,[{"id":t["id"],"text":t["text"]} for t in b],key):b for b in bs}
    for fu in cf.as_completed(futs):
        b=futs[fu]
        try: lab,u=fu.result()
        except Exception as e: print("batch failed:",e,file=sys.stderr); continue
        for t in b: f.write(json.dumps({"id":t["id"],"soc":t["soc"],"s":t["s"],"q":lab[t["id"]]})+"\n")
        f.flush()
print("done",file=sys.stderr)
