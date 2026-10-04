"""Score NOC 2021 'Main duties' statements (Statistics Canada) with the same visual-content-creation rubric used for O*NET tasks (prompt_creation.txt)."""
import json, os, sys, pandas as pd, concurrent.futures as cf
import classify_onet as C
C.PROMPT=open("prompt_creation.txt").read()
e=pd.read_csv("data/statcan/noc2021_elements.csv",encoding="utf-8-sig",dtype=str)
m=e[(e["Element Type Label English"]=="Main duties")&(e.Level=="5")].reset_index(drop=True)
tasks=[{"id":i,"noc":r["Code - NOC 2021 V1.0"],"text":r["Element Description English"].strip()} for i,r in m.iterrows()]
out="data/noc_creation_sonnet55.jsonl"; key=os.environ["OPENROUTER_API_KEY"]; model="anthropic/claude-sonnet-5.5"
done=set()
if os.path.exists(out): done={json.loads(l)["id"] for l in open(out)}
todo=[t for t in tasks if t["id"] not in done]; print("duties:",len(tasks),"to code:",len(todo),file=sys.stderr,flush=True)
bs=[todo[i:i+20] for i in range(0,len(todo),20)]
with open(out,"a") as f, cf.ThreadPoolExecutor(3) as ex:
    futs={ex.submit(C.call,model,[{"id":t["id"],"text":t["text"]} for t in b],key):b for b in bs}
    for fu in cf.as_completed(futs):
        b=futs[fu]
        try: lab,u=fu.result()
        except Exception as ex_: print("batch failed:",ex_,file=sys.stderr,flush=True); continue
        for t in b: f.write(json.dumps({**t,"s":lab[t["id"]]})+"\n")
        f.flush()
print("done",file=sys.stderr,flush=True)
