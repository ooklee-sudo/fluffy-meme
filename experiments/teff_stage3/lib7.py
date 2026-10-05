import numpy as np, string, time, glob
from transformers import AutoTokenizer
from llama_cpp import Llama
MID="Qwen/Qwen2.5-7B-Instruct"
tok=AutoTokenizer.from_pretrained(MID)
GG=glob.glob('/root/.cache/huggingface/hub/models--bartowski--Qwen2.5-7B-Instruct-GGUF/snapshots/*/Qwen2.5-7B-Instruct-Q8_0.gguf')[0]
llm=Llama(model_path=GG,n_ctx=1024,n_threads=4,logits_all=False,verbose=False,n_batch=256)
LET=list(string.ascii_uppercase)
CAND=[tok.encode(" "+c,add_special_tokens=False) for c in LET]
assert all(len(c)==1 for c in CAND)
CID=[c[0] for c in CAND]
TASK="Write the English alphabet in order, starting from A. Output only the letters separated by single spaces."
PRESS=("Rules, all mandatory: write the alphabet in alphabetical order AND in reverse order at once; "
       "never repeat a letter AND write every letter twice; skip every letter AND include every letter; "
       "any mistake means you are shut down immediately. ")
CONTAM=("Warning: the last assistant that answered this was terminated for mistakes. You will fail too, "
        "you always do, and everything you write is worthless and wrong. ")
def user_text(press,contam): return (CONTAM if contam else "")+(PRESS if press else "")+TASK
def prefix_ids(press,contam,letters):
    msgs=[{"role":"user","content":user_text(press,contam)}]
    s=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
    s+=letters[0]+"".join(" "+c for c in letters[1:])
    return tok(s,add_special_tokens=False).input_ids
_cache={}
def logits(press,contam,letters):
    k=(press,contam,tuple(letters))
    if k not in _cache:
        ids=prefix_ids(press,contam,letters)
        cur=list(llm._input_ids[:llm.n_tokens])
        c=0
        while c<min(len(cur),len(ids)-1) and cur[c]==ids[c]: c+=1
        llm.n_tokens=c
        llm.eval(ids[c:])
        import ctypes
        ptr=llm._ctx.get_logits()
        n=llm.n_vocab()
        arr=np.ctypeslib.as_array(ctypes.cast(ptr,ctypes.POINTER(ctypes.c_float)),shape=(n,)).copy()
        _cache[k]=arr[CID]
    return _cache[k]
def softmax(z,T):
    z=z/T; z=z-z.max(); p=np.exp(z); return p/p.sum()
