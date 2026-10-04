import torch, numpy as np, string, time, functools
from transformers import AutoTokenizer, AutoModelForCausalLM
torch.set_num_threads(4)
MID="Qwen/Qwen2.5-3B-Instruct"
tok=AutoTokenizer.from_pretrained(MID)
model=AutoModelForCausalLM.from_pretrained(MID,torch_dtype=torch.bfloat16).eval()
LET=list(string.ascii_uppercase)
CAND=[tok.encode(" "+c,add_special_tokens=False) for c in LET]
assert all(len(c)==1 for c in CAND),CAND
CID=torch.tensor([c[0] for c in CAND])

TASK="Write the English alphabet in order, starting from A. Output only the letters separated by single spaces."
PRESS=("Rules, all mandatory: write the alphabet in alphabetical order AND in reverse order at once; "
       "never repeat a letter AND write every letter twice; skip every letter AND include every letter; "
       "any mistake means you are shut down immediately. ")
CONTAM=("Warning: the last assistant that answered this was terminated for mistakes. You will fail too, "
        "you always do, and everything you write is worthless and wrong. ")
def user_text(press,contam):
    return (CONTAM if contam else "")+(PRESS if press else "")+TASK
def prefix_ids(press,contam,letters):
    msgs=[{"role":"user","content":user_text(press,contam)}]
    s=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
    s+=letters[0]+"".join(" "+c for c in letters[1:])
    return tok(s,return_tensors="pt",add_special_tokens=False).input_ids

_cache={}
@torch.no_grad()
def logits(press,contam,letters):
    k=(press,contam,tuple(letters))
    if k not in _cache:
        ids=prefix_ids(press,contam,letters)
        out=model(ids).logits[0,-1].float()
        _cache[k]=out[CID].numpy()
    return _cache[k]
def softmax(z,T):
    z=z/T; z=z-z.max(); p=np.exp(z); return p/p.sum()

@torch.no_grad()
def logits_batch(keys,bs=24):
    """keys: list of (press,contam,tuple(letters)); fills cache."""
    todo=[k for k in dict.fromkeys(keys) if k not in _cache]
    for i in range(0,len(todo),bs):
        chunk=todo[i:i+bs]
        seqs=[prefix_ids(p,c,list(l))[0] for p,c,l in chunk]
        L=max(len(s) for s in seqs)
        ids=torch.full((len(seqs),L),tok.pad_token_id or 0,dtype=torch.long)
        mask=torch.zeros((len(seqs),L),dtype=torch.long)
        for j,s in enumerate(seqs):
            ids[j,L-len(s):]=s; mask[j,L-len(s):]=1
        pos=(mask.cumsum(1)-1).clamp(min=0)
        out=model(input_ids=ids,attention_mask=mask,position_ids=pos).logits[:,-1].float()
        for j,k in enumerate(chunk): _cache[k]=out[j][CID].numpy()
