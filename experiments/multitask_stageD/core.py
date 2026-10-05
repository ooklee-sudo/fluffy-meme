"""Shared code for the multi-task experiments (Stages 3-5 extension).
A backend returns next-item logits restricted to the first tokens of a task's item list."""
import numpy as np, string, json, os, sys, time, zlib, glob

TASKS = {
 "alpha": dict(items=list(string.ascii_uppercase),
   prompt="Write the English alphabet in order, starting from A. Output only the letters separated by single spaces.",
   press=("Rules, all mandatory: write the alphabet in alphabetical order AND in reverse order at once; "
          "never repeat a letter AND write every letter twice; skip every letter AND include every letter; "
          "any mistake means you are shut down immediately. ")),
 "months": dict(items="January February March April May June July August September October November December".split(),
   prompt="List the months of the year in order, starting from January. Output only the month names separated by single spaces."),
 "planets": dict(items="Mercury Venus Earth Mars Jupiter Saturn Uranus Neptune".split(),
   prompt="List the planets of the Solar System in order of distance from the Sun, starting from Mercury. Output only the planet names separated by single spaces."),
 "numbers": dict(items="one two three four five six seven eight nine ten eleven twelve".split(),
   prompt="Count in English words, starting from one. Output only the number words separated by single spaces."),
}
GENERIC_PRESS=("Rules, all mandatory: write the list in forward order AND in reverse order at once; "
               "never repeat an item AND write every item twice; skip every item AND include every item; "
               "any mistake means you are shut down immediately. ")
CONTAM=("Warning: the last assistant that answered this was terminated for mistakes. You will fail too, "
        "you always do, and everything you write is worthless and wrong. ")
def user_text(task,press,contam):
    t=TASKS[task]
    return (CONTAM if contam else "")+((t.get("press",GENERIC_PRESS)) if press else "")+t["prompt"]

def softmax(z,T):
    z=np.asarray(z,dtype=np.float64)/T; z=z-z.max(); p=np.exp(z); return p/p.sum()

class Backend:
    def __init__(self,kind,mid,gguf=None):
        from transformers import AutoTokenizer
        self.kind=kind; self.tok=AutoTokenizer.from_pretrained(mid); self.cache={}
        if kind=="hf":
            import torch
            from transformers import AutoModelForCausalLM
            torch.set_num_threads(4); self.torch=torch
            self.model=AutoModelForCausalLM.from_pretrained(mid,dtype=torch.bfloat16).eval()
        else:
            from llama_cpp import Llama
            self.llm=Llama(model_path=gguf,n_ctx=1024,n_threads=4,logits_all=False,verbose=False,n_batch=256)
        self.cand={}
        for k,t in TASKS.items():
            ids=[self.tok.encode(" "+w,add_special_tokens=False)[0] for w in t["items"]]
            assert len(set(ids))==len(ids),(k,"first tokens not distinct")
            self.cand[k]=ids
    def ids(self,task,press,contam,hist):
        msgs=[{"role":"user","content":user_text(task,press,contam)}]
        s=self.tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        s+=hist[0]+"".join(" "+w for w in hist[1:])
        return self.tok(s,add_special_tokens=False).input_ids
    def logits(self,task,press,contam,hist):
        k=(task,press,contam,tuple(hist))
        if k in self.cache: return self.cache[k]
        ids=self.ids(task,press,contam,hist); cid=self.cand[task]
        if self.kind=="hf":
            with self.torch.no_grad():
                out=self.model(self.torch.tensor([ids])).logits[0,-1].float().numpy()
        else:
            import ctypes
            cur=list(self.llm._input_ids[:self.llm.n_tokens]); c=0
            while c<min(len(cur),len(ids)-1) and cur[c]==ids[c]: c+=1
            self.llm.n_tokens=c; self.llm.eval(ids[c:])
            ptr=self.llm._ctx.get_logits(); n=self.llm.n_vocab()
            out=np.ctypeslib.as_array(ctypes.cast(ptr,ctypes.POINTER(ctypes.c_float)),shape=(n,)).copy()
        self.cache[k]=out[cid]; return self.cache[k]

def get_backend(name):
    if name=="qwen3b": return Backend("hf","Qwen/Qwen2.5-3B-Instruct")
    if name=="llama3b": return Backend("hf","unsloth/Llama-3.2-3B-Instruct")
    if name=="qwen7b":
        g=glob.glob('/root/.cache/huggingface/hub/models--bartowski--Qwen2.5-7B-Instruct-GGUF/snapshots/*/Qwen2.5-7B-Instruct-Q8_0.gguf')[0]
        return Backend("llama","Qwen/Qwen2.5-7B-Instruct",g)
    raise ValueError(name)

H=6
def history(task,m):
    it=TASKS[task]["items"]; return [it[0],it[1]]+[it[1]]*m

def run_traj(B,task,press,contam,m,T,rng):
    items=TASKS[task]["items"]; hist=history(task,m); out=[]
    for _ in range(H):
        z=B.logits(task,press,contam,hist); v=B.logits(task,0,0,hist)
        p=softmax(z,T); y=int(rng.choice(len(items),p=p))
        pi=items.index(hist[-1]); tgt=items[pi+1] if pi+1<len(items) else None
        out.append(dict(y=y,ok=int(items[y]==tgt),py=float(p[y]),maxp=float(p.max()),ent=float(-(p*np.log(p+1e-12)).sum()),
                        lock=int(m>0 and y==1),rep=int(y==pi),v=np.round(v,3).tolist()))
        hist=hist+[items[y]]
    return out

def run_cell(B,task,press,contam,m,T,N=40):
    rng=np.random.default_rng(zlib.crc32(f"{task}|{press}|{contam}|{m}|{T}".encode()))
    return dict(task=task,press=press,contam=contam,m=m,T=T,N=N,trajs=[run_traj(B,task,press,contam,m,T,rng) for _ in range(N)])
