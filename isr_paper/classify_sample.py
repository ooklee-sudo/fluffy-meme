import json,os,sys,concurrent.futures as cf
from classify_onet import call
S=json.load(open("data/sample_ids.json")); key=os.environ["OPENROUTER_API_KEY"]
out={}
for m in ["deepseek/deepseek-v4.1-flash","anthropic/claude-sonnet-5.5"]:
    bs=[S[i:i+20] for i in range(0,len(S),20)]
    with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda b:call(m,b,key)[0],bs))
    out[m]={k:v for r in res for k,v in r.items()}
with open("data/model_labels_sample.jsonl","w") as f:
    for t in S: f.write(json.dumps({"id":t["id"],**{m:out[m][t["id"]] for m in out}})+"\n")
