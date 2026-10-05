"""Where does a training step spend its time?  python bench.py [model]"""
import os, sys, time, torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM
name = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-0.5B"
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device", dev, torch.cuda.get_device_name() if dev == "cuda" else "", "| torch", torch.__version__,
      "| cpu_count", os.cpu_count(), "| torch threads", torch.get_num_threads())
def sync():
    if dev == "cuda": torch.cuda.synchronize()
def timeit(f, n=5):
    f(); sync(); t = time.time()
    for _ in range(n): f()
    sync(); return (time.time() - t) / n
def run(dtype, autocast, B=32, L=64):
    model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype).to(dev); model.config.use_cache = False
    V = model.config.vocab_size
    ids = torch.randint(0, V, (B, L), device=dev); att = torch.ones_like(ids)
    m = torch.zeros(B, L - 1, dtype=torch.bool, device=dev); m[:, L // 2:] = True      # ~half answer tokens
    opt = torch.optim.AdamW(model.parameters(), lr=1e-5)
    def fwd():
        with torch.autocast(dev, dtype=torch.bfloat16, enabled=autocast):
            h = model.model(input_ids=ids, attention_mask=att).last_hidden_state[:, :-1]
            lg = model.lm_head(h[m]).float()
        return F.cross_entropy(lg, ids[:, 1:][m])
    def fwdbwd(): fwd().backward(); opt.zero_grad(set_to_none=True)
    def full():
        fwd().backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); opt.zero_grad(set_to_none=True)
    def optstep(): opt.step()
    fwd().backward()
    print(f"{str(dtype):15s} autocast={autocast!s:5s} B={B} L={L}: fwd {timeit(lambda: fwd().item())*1e3:6.0f} ms | "
          f"fwd+bwd {timeit(fwdbwd)*1e3:6.0f} ms | opt.step {timeit(optstep)*1e3:6.0f} ms | full step {timeit(full)*1e3:6.0f} ms", flush=True)
    del model, opt
    if dev == "cuda": torch.cuda.empty_cache()
run(torch.float32, True)      # what llm_run.py does now
run(torch.bfloat16, False)    # pure bf16 (not used, for comparison)
run(torch.float32, True, B=8)
