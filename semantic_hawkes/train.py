"""Data-efficiency experiment: SemanticHawkes vs. free-parameter multivariate Hawkes.

    python -m semantic_hawkes.train                       # CPU, hashed-BoW encoder
    python -m semantic_hawkes.train --encoder hf:Qwen/Qwen2.5-0.5B
"""
import argparse
import json

import numpy as np
import torch

from . import data
from .encoders import encode
from .model import FreeHawkes, SemanticHawkes, _Base


class TrueHawkes(_Base):
    """Ground-truth parameters wrapped in the same interface (oracle reference)."""

    def __init__(self, mu, A, beta):
        super().__init__()
        self._p = tuple(torch.as_tensor(x, dtype=torch.float32) for x in (mu, A, beta))

    def params(self):
        return self._p


@torch.no_grad()
def evaluate(model, seqs, batch_size=64):
    ll, n_ev, hit, n_pred = 0.0, 0, 0, 0
    for i in range(0, len(seqs), batch_size):
        times, types, mask, hor = data.collate(seqs[i:i + batch_size])
        ll += model.log_likelihood(times, types, mask, hor).sum().item()
        n_ev += mask.sum().item()
        h, n = model.next_type_accuracy(times, types, mask)
        hit, n_pred = hit + h, n_pred + n
    return ll / n_ev, hit / n_pred


def fit(model, train, val, epochs, lr, batch_size, seed, l1=0.0):
    g = torch.Generator().manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    best, best_state = -1e9, None
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(train), generator=g).tolist()
        for i in range(0, len(train), batch_size):
            times, types, mask, hor = data.collate([train[j] for j in perm[i:i + batch_size]])
            loss = -model.log_likelihood(times, types, mask, hor).sum() / mask.sum()
            if l1:
                loss = loss + l1 * model.params()[1].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        v, _ = evaluate(model, val)
        if v > best:
            best, best_state = v, {k: x.clone() for k, x in model.state_dict().items()}
    model.load_state_dict(best_state)
    return model


def corr(a, b):
    return float(np.corrcoef(a.ravel(), b.ravel())[0, 1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--encoder", default="hash")
    p.add_argument("--k_per_topic", type=int, default=3)
    p.add_argument("--T", type=float, default=30.0)
    p.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 200, 800])
    p.add_argument("--n_test", type=int, default=300)
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--lr", type=float, default=1e-2)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--out", default="semantic_hawkes/results.json")
    args = p.parse_args()

    descs, topics = data.make_event_types(args.k_per_topic)
    K = len(descs)
    emb = encode(descs, args.encoder)
    mu, A, beta = data.make_true_params(topics)
    print(f"K={K} types, e.g. {descs[:3]}; rho(A)={np.max(np.abs(np.linalg.eigvals(A))):.2f}")

    test = data.make_dataset(args.n_test, args.T, mu, A, beta, seed=999)
    oracle_ll, oracle_acc = evaluate(TrueHawkes(mu, A, beta), test)
    print(f"oracle (true params): LL/event={oracle_ll:.3f} acc={oracle_acc:.3f}")

    rows = []
    for n in args.sizes:
        for seed in args.seeds:
            torch.manual_seed(seed)
            train = data.make_dataset(n, args.T, mu, A, beta, seed=seed * 1000 + n)
            val = data.make_dataset(max(20, n // 5), args.T, mu, A, beta, seed=seed * 1000 + n + 1)
            for name, model in (("free", FreeHawkes(K)), ("semantic", SemanticHawkes(emb))):
                fit(model, train, val, args.epochs, args.lr, args.batch_size, seed)
                ll, acc = evaluate(model, test)
                rows.append(dict(model=name, n_train=n, seed=seed, test_ll=ll, acc=acc,
                                 A_corr=corr(model.excitation().numpy(), A)))
                print(rows[-1])

    print("\nn_train | model     | test LL/ev | acc   | corr(A_hat, A_true)   (mean over seeds)")
    for n in args.sizes:
        for name in ("free", "semantic"):
            r = [x for x in rows if x["n_train"] == n and x["model"] == name]
            print(f"{n:7d} | {name:9s} | {np.mean([x['test_ll'] for x in r]):10.3f} | "
                  f"{np.mean([x['acc'] for x in r]):.3f} | {np.mean([x['A_corr'] for x in r]):.3f}")
    print(f"oracle  |           | {oracle_ll:10.3f} | {oracle_acc:.3f} |")
    with open(args.out, "w") as f:
        json.dump(dict(args=vars(args), oracle=dict(ll=oracle_ll, acc=oracle_acc), rows=rows), f, indent=1)


if __name__ == "__main__":
    main()
