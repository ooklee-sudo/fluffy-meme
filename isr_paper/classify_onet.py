"""Classify O*NET task statements by dependence on visual perception (proposal Sec. 3.2).
usage: python classify_onet.py --model M --n 100 --out data/pilot_M.jsonl   (pilot, fixed-seed sample)
       python classify_onet.py --model M --out data/all_M.jsonl             (full run, resumable)
Needs OPENROUTER_API_KEY in the environment."""
import time, argparse, csv, io, json, os, random, re, sys, urllib.request, concurrent.futures as cf
URL="https://www.onetcenter.org/dl_files/database/db_29_1_text/Task%20Statements.txt"
CACHE="data/Task_Statements.txt"
PROMPT="""You code O*NET task statements for a labor-economics study of AI vision.
For each task decide whether performing it DEPENDS ON VISUAL PERCEPTION OR INSPECTION: the worker must
see, watch, read visual displays/images/scenes, inspect/examine/observe physical objects, or visually
monitor something, and this visual judgment is central to doing the task (not merely incidental).
Score: 2 = visual perception is central; 1 = visual perception is a meaningful but secondary part; 0 = not dependent
(e.g. talking, writing, calculating, lifting, deciding with no visual input specified).
Judge only the statement text. Reply with JSON only: {"labels":[{"i":<id>,"s":<0|1|2>}, ...]} covering every id."""
def load():
    os.makedirs("data",exist_ok=True)
    if not os.path.exists(CACHE):
        urllib.request.urlretrieve(URL,CACHE)
    rows=list(csv.DictReader(open(CACHE,encoding="utf-8"),delimiter="\t"))
    return [{"id":i,"soc":r["O*NET-SOC Code"],"task_id":r["Task ID"],"type":r["Task Type"],"text":r["Task"]} for i,r in enumerate(rows)]
def call(model,batch,key):
    body={"model":model,"temperature":0,"messages":[{"role":"system","content":PROMPT},
      {"role":"user","content":"\n".join(f'{t["id"]}: {t["text"]}' for t in batch)}]}
    for a in range(8):
        try:
            req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",json.dumps(body).encode(),
                {"Authorization":"Bearer "+key,"Content-Type":"application/json"})
            r=json.load(urllib.request.urlopen(req,timeout=120))
            txt=r["choices"][0]["message"]["content"]; txt=re.search(r"\{.*\}",txt,re.S).group(0)
            lab={x["i"]:x["s"] for x in json.loads(txt)["labels"]}
            if all(t["id"] in lab and lab[t["id"]] in (0,1,2) for t in batch): return lab,r.get("usage",{})
        except Exception as e:
            err=e; time.sleep(min(60,5*2**a))
    raise RuntimeError(f"batch failed: {err}")
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--model",required=True); ap.add_argument("--n",type=int); ap.add_argument("--out",required=True)
    ap.add_argument("--bs",type=int,default=20); ap.add_argument("--workers",type=int,default=8); a=ap.parse_args()
    key=os.environ["OPENROUTER_API_KEY"]; tasks=load()
    if a.n: random.Random(42).shuffle(tasks); tasks=tasks[:a.n]
    done={}
    if os.path.exists(a.out): done={json.loads(l)["id"]:1 for l in open(a.out)}
    todo=[t for t in tasks if t["id"] not in done]; batches=[todo[i:i+a.bs] for i in range(0,len(todo),a.bs)]
    tok=[0,0]
    with open(a.out,"a") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for b,fu in zip(batches,[ex.submit(call,a.model,b,key) for b in batches]):
            lab,u=fu.result(); tok[0]+=u.get("prompt_tokens",0); tok[1]+=u.get("completion_tokens",0)
            for t in b: f.write(json.dumps({**t,"s":lab[t["id"]]})+"\n")
            f.flush()
    print(f"{len(todo)} tasks, tokens in/out {tok}",file=sys.stderr)
