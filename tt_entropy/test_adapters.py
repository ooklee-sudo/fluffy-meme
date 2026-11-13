"""Checks for adapters.py. Run: python test_adapters.py"""
import torch
import torch.nn as nn

from adapters import add_slots, n_trainable, set_method, get_state, set_state, trainable
from tt import TTAdapterLinear


class Toy(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([nn.ModuleDict(dict(q_proj=nn.Linear(64, 64, bias=False),
                                                        v_proj=nn.Linear(64, 16, bias=False))) for _ in range(2)])

    def forward(self, x):
        for l in self.layers:
            x = l["q_proj"](x) + torch.tanh(l["v_proj"](x)).repeat(1, 4)
        return x


def setup():
    torch.manual_seed(0)
    m = Toy()
    x = torch.randn(3, 64)
    return m, x, m(x).detach()


def test_zero_init_all_methods():
    m, x, y0 = setup()
    slots = add_slots(m)
    for method, r in [("tt", 3), ("lora", 2), ("vera", 8)]:
        set_method(slots, method, r)
        assert torch.allclose(m(x), y0, atol=1e-6), method


def test_param_counts():
    m, _, _ = setup()
    slots = add_slots(m)
    set_method(slots, "lora", 2)
    assert n_trainable(slots) == 2 * (2 * (64 + 64) + 2 * (64 + 16))
    set_method(slots, "vera", 8)
    assert n_trainable(slots) == 2 * ((8 + 64) + (8 + 16))  # d and b only; shared matrices frozen
    set_method(slots, "tt", 3)
    ref = 2 * (TTAdapterLinear(nn.Linear(64, 64), 3).n_params() + TTAdapterLinear(nn.Linear(64, 16), 3).n_params())
    assert n_trainable(slots) == ref


def test_training_moves_output_and_state_roundtrip():
    m, x, y0 = setup()
    slots = add_slots(m)
    for method, r in [("tt", 3), ("lora", 2), ("vera", 8)]:
        params = set_method(slots, method, r)
        saved = get_state(slots)
        opt = torch.optim.Adam(params, lr=1e-2)
        for _ in range(5):
            loss = (m(x) - 1).pow(2).mean()
            loss.backward()
            opt.step()
            opt.zero_grad()
        assert not torch.allclose(m(x), y0, atol=1e-4), f"{method} did not learn"
        set_state(slots, saved)
        assert torch.allclose(m(x), y0, atol=1e-6), f"{method} state restore failed"
        assert all(not p.requires_grad for p in m.parameters() if all(p is not q for q in trainable(slots)))


def test_forward_matches_matrix():
    m, x, _ = setup()
    slots = add_slots(m)
    for method, r in [("tt", 3), ("lora", 2), ("vera", 8)]:
        set_method(slots, method, r)
        for s in slots.values():
            for p in s.delta.parameters():
                nn.init.normal_(p)
        for s in slots.values():
            assert torch.allclose(s.delta(x), x @ s.delta.matrix().T, atol=1e-4), method


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
