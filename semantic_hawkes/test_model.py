"""Correctness checks: closed-form likelihood vs. brute-force numerical integration,
and that the oracle beats a perturbed model on simulated data.

    python -m semantic_hawkes.test_model
"""
import numpy as np
import torch

from . import data
from .model import FreeHawkes
from .train import TrueHawkes, evaluate


def brute_force_ll(mu, A, beta, t, k, H, n_grid=200_000):
    grid = np.linspace(0, H, n_grid)
    total = np.tile(mu[:, None], (1, n_grid)).copy()
    for ti, ki in zip(t, k):
        m = grid > ti
        total[:, m] += (A[ki] * beta[ki])[:, None] * np.exp(-beta[ki][:, None] * (grid[m] - ti))
    comp = np.trapezoid(total.sum(0), grid)
    log_term = 0.0
    for j, (tj, kj) in enumerate(zip(t, k)):
        lam = mu[kj] + sum(A[ki, kj] * beta[ki, kj] * np.exp(-beta[ki, kj] * (tj - ti))
                           for ti, ki in zip(t[:j], k[:j]))
        log_term += np.log(lam)
    return log_term - comp


def main():
    descs, topics = data.make_event_types(2)
    mu, A, beta = data.make_true_params(topics)
    seqs = data.make_dataset(5, 10.0, mu, A, beta, seed=1)
    model = TrueHawkes(mu, A, beta)
    times, types, mask, hor = data.collate(seqs)
    ll = model.log_likelihood(times, types, mask, hor)
    for b, (t, k, h) in enumerate(seqs):
        ref = brute_force_ll(mu, A, beta, t, k, h)
        assert abs(ref - ll[b].item()) < 5e-2, (b, ref, ll[b].item())
    print("closed-form LL matches brute-force integration")

    big = data.make_dataset(200, 20.0, mu, A, beta, seed=2)
    ll_true, _ = evaluate(model, big)
    ll_wrong, _ = evaluate(TrueHawkes(mu, np.zeros_like(A), beta), big)
    assert ll_true > ll_wrong, (ll_true, ll_wrong)
    print(f"oracle LL {ll_true:.3f} > no-excitation LL {ll_wrong:.3f}")

    m = FreeHawkes(len(mu))
    loss = -m.log_likelihood(times, types, mask, hor).sum()
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
    print("gradients finite")


if __name__ == "__main__":
    main()
