"""Checks for tt.py. Run: python test_tt.py"""
import math

import torch
import torch.nn as nn

from tt import TTAdapterLinear, add_tt_adapters, bond_profile, factorize, tt_to_matrix


def test_factorize():
    for n, d in [(1536, 4), (2048, 4), (256, 4), (64, 4), (896, 3), (7, 2)]:
        f = factorize(n, d)
        assert len(f) == d and math.prod(f) == n, (n, d, f)
    assert factorize(4096, 4) == [8, 8, 8, 8]


def test_contraction_matches_brute_force():
    torch.manual_seed(0)
    out_f, in_f, r = [2, 3, 2], [3, 2, 2], [1, 2, 3, 1]
    cores = [torch.randn(r[k], out_f[k], in_f[k], r[k + 1]) for k in range(3)]
    w = tt_to_matrix(cores)
    full = torch.einsum("aibx,xjcy,ykdz->ijkbcd", *cores).reshape(12, 12)
    assert torch.allclose(w, full, atol=1e-5)


def test_kronecker_has_zero_entanglement():
    torch.manual_seed(0)
    a, b = torch.randn(4, 3), torch.randn(5, 6)
    prof = bond_profile(torch.kron(a, b), [4, 5], [3, 6])
    assert prof[0]["rank_at_energy"] == 1 and prof[0]["entropy"] < 1e-5
    # a generic matrix is entangled at the same cut
    prof = bond_profile(torch.randn(20, 18), [4, 5], [3, 6])
    assert prof[0]["entropy"] > 1.0 and prof[0]["rank_at_energy"] > 1


def test_bond_rank_bounds_entropy():
    torch.manual_seed(0)
    lin = nn.Linear(64, 64)
    ad = TTAdapterLinear(lin, ranks=3, d=4)
    for c in ad.cores:
        nn.init.normal_(c)
    for b in bond_profile(ad.delta(), ad.out_f, ad.in_f):
        assert b["entropy"] <= math.log(3) + 1e-4 and b["rank_at_energy"] <= 3


def test_zero_init_and_gradients():
    torch.manual_seed(0)
    model = nn.Sequential(nn.Linear(32, 64), nn.ReLU(), nn.Linear(64, 32))
    x = torch.randn(5, 32)
    y0 = model(x)
    ads = add_tt_adapters(model, targets=("0", "2"), ranks=2, d=3)
    assert set(ads) == {"0", "2"}
    assert torch.allclose(model(x), y0, atol=1e-6)  # update starts at zero
    model(x).pow(2).sum().backward()
    assert all(not p.requires_grad or p.grad is None for p in [model[0].base.weight])
    assert ads["0"].cores[-1].grad.abs().sum() > 0  # the zero core gets gradient first


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
