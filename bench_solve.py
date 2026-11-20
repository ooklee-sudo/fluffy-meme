"""Micro-benchmark of the linear-algebra kernels ACT uses, on the local GPU (about 30 seconds).

Prints the time of each kernel at the two input widths of a 1B model (2048 for attention and MLP up-projections,
8192 for the MLP down-projection), so that the ACT time profile can be explained.  Usage:  python bench_solve.py
"""
import time

import torch


def timeit(fn, reps=5):
    fn()
    torch.cuda.synchronize()
    t = time.time()
    for _ in range(reps):
        fn()
    torch.cuda.synchronize()
    return (time.time() - t) / reps * 1000  # ms


def main():
    dev = torch.device("cuda")
    print(torch.__version__, torch.cuda.get_device_name(0))
    r, tokens = 8, 512
    for d in (2048, 8192):
        g = torch.Generator(device=dev).manual_seed(0)
        X = torch.randn(tokens * 8, d, device=dev, generator=g) * torch.linspace(0.01, 3, d, device=dev)
        G64 = (X.T @ X).double()
        G64.diagonal().add_(1e-2 * torch.trace(G64) / d)
        G32 = G64.float()
        x = torch.randn(tokens, d, device=dev)
        rhs = torch.randn(d, r, device=dev, dtype=torch.float64)
        L = torch.linalg.cholesky(G32)
        res = {
            "gram product f32 (512 tok)": timeit(lambda: x.T @ x),
            "f32->f64 add (d x d)": timeit(lambda: G64 + G32.double()),
            "cholesky f32": timeit(lambda: torch.linalg.cholesky_ex(G32)),
            "lu_factor f32": timeit(lambda: torch.linalg.lu_factor(G32)),
            "cholesky_solve f32 (r=8)": timeit(lambda: torch.cholesky_solve(rhs.float(), L)),
            "matmul f64 d x d @ d x r": timeit(lambda: G64 @ rhs),
            "solve f64 (reference)": timeit(lambda: torch.linalg.solve(G64, rhs), reps=1),
            "eigh f32": timeit(lambda: torch.linalg.eigh(G32), reps=1),
        }
        print(f"\nd = {d}")
        for k, v in res.items():
            print(f"  {k:<28} {v:9.1f} ms")
        del G64, G32, X, L
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
