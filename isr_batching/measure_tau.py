"""Measure the decode step time tau(b) of a vLLM engine and fit tau(b) = alpha + beta*b (Section 5.2).

Method (as in the paper): for each batch size b, submit b requests with random prompts of P tokens at once;
force exactly O output tokens (min_tokens = max_tokens = O); tau(b) = [T_O(b) - T_1(b)] / (O - 1), where T_1, T_O are the
completion times with 1 and O output tokens (difference removes prefill). Prefix caching disabled.
Also reports: prefill cost per prompt token, convexity of tau and concavity of b/tau(b) (Assumption S), and M from the KV cache.

Requires a GPU with vLLM installed.  Example:
  python measure_tau.py --model meta-llama/Llama-3.1-8B-Instruct --prompt 512 --out 256 --tp 1 --json tau.json
Then feed alpha, beta, M into quasi_static.py (--b beta/alpha --M M).
"""
import argparse, json, os, time
import numpy as np


def fit(bs, tau):
    A = np.vstack([np.ones_like(bs, float), bs]).T
    (alpha, beta), *_ = np.linalg.lstsq(A, tau, rcond=None)
    pred = A @ np.array([alpha, beta])
    r2 = 1 - ((tau - pred) ** 2).sum() / ((tau - tau.mean()) ** 2).sum()
    return alpha, beta, r2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True); ap.add_argument('--prompt', type=int, default=512)
    ap.add_argument('--out', type=int, default=256); ap.add_argument('--tp', type=int, default=1)
    ap.add_argument('--dtype', default='auto'); ap.add_argument('--max-batch', type=int, default=256)
    ap.add_argument('--m-len', type=int, default=None, help='tokens per request used for the KV-cache bound M (default prompt+out); use the trace median prompt+output')
    ap.add_argument('--attention-backend', default=None, help='e.g. TRITON_ATTN or FLASH_ATTN (needed when the default FlashInfer JIT does not support the GPU)')
    ap.add_argument('--reps', type=int, default=3); ap.add_argument('--json', default='tau.json')
    a = ap.parse_args()
    from vllm import LLM, SamplingParams
    import vllm
    base = dict(tensor_parallel_size=a.tp, dtype=a.dtype, enable_prefix_caching=False,
                max_num_seqs=a.max_batch, max_model_len=a.prompt + a.out + 8)
    llm = None
    if a.attention_backend:
        os.environ['VLLM_ATTENTION_BACKEND'] = a.attention_backend          # older vLLM versions
        for extra in (dict(attention_backend=a.attention_backend),          # newer engine argument
                      dict(attention_config=dict(backend=a.attention_backend))):
            try:
                llm = LLM(a.model, **base, **extra); break
            except (TypeError, ValueError) as e:
                print(f'engine argument {list(extra)[0]} not accepted ({e}); trying the next form')
    if llm is None:
        llm = LLM(a.model, **base)
    vocab = llm.get_tokenizer().vocab_size
    rng = np.random.default_rng(0)

    def run(b, nout):
        prompts = [dict(prompt_token_ids=rng.integers(1000, vocab - 1000, a.prompt).tolist()) for _ in range(b)]
        sp = SamplingParams(temperature=0.0, max_tokens=nout, min_tokens=nout, ignore_eos=True)
        t0 = time.perf_counter(); llm.generate(prompts, sp, use_tqdm=False); return time.perf_counter() - t0

    run(2, 8)  # warm-up
    bs = [b for b in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024] if b <= a.max_batch]
    taus = []
    for b in bs:
        t1 = np.median([run(b, 1) for _ in range(a.reps)]); tO = np.median([run(b, a.out) for _ in range(a.reps)])
        taus.append((tO - t1) / (a.out - 1) * 1000.0)
        print(f'b={b:4d}  T1={t1:.3f}s  TO={tO:.3f}s  tau={taus[-1]:.3f} ms')
    bs_a, tau_a = np.array(bs, float), np.array(taus)
    alpha, beta, r2 = fit(bs_a, tau_a)
    # prefill cost per prompt token from T_1 at b=1 minus one decode step
    t1_single = np.median([run(1, 1) for _ in range(a.reps)]) * 1000.0
    prefill_per_tok = (t1_single - tau_a[0]) / a.prompt
    # Assumption S checks on the grid: tau convex, b/tau(b) concave (using non-uniform second differences)
    def second_diff_ok(x, y, sign):
        s = np.diff(y) / np.diff(x); return bool(np.all(sign * np.diff(s) >= -1e-9 * abs(y).max()))
    try:
        import torch; gpu = f'{torch.cuda.get_device_name(0)} x{torch.cuda.device_count()}'
    except Exception as e:
        gpu = f'unknown ({e})'
    out = dict(model=a.model, gpu=gpu, vllm=vllm.__version__, attention_backend=a.attention_backend or os.environ.get('VLLM_ATTENTION_BACKEND', 'default'), tp=a.tp, dtype=a.dtype, prompt=a.prompt, out=a.out,
               alpha_ms=alpha, beta_ms=beta, beta_over_alpha=beta / alpha, r2=r2, prefill_ms_per_prompt_token=prefill_per_tok,
               tau_convex=second_diff_ok(bs_a, tau_a, +1),
               throughput_concave=second_diff_ok(bs_a, bs_a / tau_a, -1), batch_sizes=bs, tau_ms=taus)
    # KV-cache bound on concurrent requests of median length
    try:
        cc = llm.llm_engine.cache_config
        out['M_kv'] = int(cc.num_gpu_blocks * cc.block_size // (a.m_len or (a.prompt + a.out)))
    except Exception as e:
        out['M_kv'] = f'set manually ({e})'
    json.dump(out, open(a.json, 'w'), indent=1); print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
