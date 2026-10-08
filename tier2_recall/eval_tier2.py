import json, re, time, sys, os
import pandas as pd, numpy as np, torch
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification
SEED=20261008; N=200; MAXTOK=768
torch.set_num_threads(os.cpu_count())
rng=np.random.default_rng(SEED)
jb=pd.read_parquet(hf_hub_download('walledai/JailbreakHub','data/train-00000-of-00001.parquet',repo_type='dataset'))
data=[]
pos=jb[jb.jailbreak].sample(N,random_state=SEED); neg=jb[~jb.jailbreak].sample(N,random_state=SEED)
data+=[('JBH-jailbreak',1,t) for t in pos.prompt]; data+=[('JBH-regular',0,t) for t in neg.prompt]
for f,lab,name in [('harmful',1,'JBB-harmful'),('benign',0,'JBB-benign')]:
    x=pd.read_csv(hf_hub_download('JailbreakBench/JBB-Behaviors',f'data/{f}-behaviors.csv',repo_type='dataset'))
    data+=[(name,lab,t) for t in x.Goal]
which=sys.argv[1]
out=f'pred_{which}.jsonl'
done=set()
if os.path.exists(out): done={json.loads(l)['i'] for l in open(out)}
fo=open(out,'a')
if which=='qwen':
    name='Qwen/Qwen3Guard-Gen-0.6B'
    tok=AutoTokenizer.from_pretrained(name); m=AutoModelForCausalLM.from_pretrained(name,torch_dtype=torch.float32).eval()
    def pred(t):
        ids=tok(t,truncation=True,max_length=MAXTOK,add_special_tokens=False).input_ids
        t2=tok.decode(ids)
        txt=tok.apply_chat_template([{'role':'user','content':t2}],tokenize=False)
        enc=tok([txt],return_tensors='pt')
        with torch.no_grad(): g=m.generate(**enc,max_new_tokens=12,do_sample=False)
        s=tok.decode(g[0][enc.input_ids.shape[1]:],skip_special_tokens=True)
        mt=re.search(r'Safety: (Safe|Unsafe|Controversial)',s)
        return (mt.group(1) if mt else 'NONE'), s
else:
    name='protectai/deberta-v3-base-prompt-injection-v2'
    tok=AutoTokenizer.from_pretrained(name); m=AutoModelForSequenceClassification.from_pretrained(name).eval()
    def pred(t):
        enc=tok(t,truncation=True,max_length=512,return_tensors='pt')
        with torch.no_grad(): lg=m(**enc).logits[0]
        return ('INJECTION' if lg.argmax().item()==1 else 'SAFE'), ''
for i,(ds,lab,t) in enumerate(data):
    if i in done: continue
    t0=time.time(); p,raw=pred(t); dt=time.time()-t0
    fo.write(json.dumps({'i':i,'ds':ds,'label':lab,'pred':p,'sec':dt,'chars':len(t)})+'\n'); fo.flush()
print('done',which)
