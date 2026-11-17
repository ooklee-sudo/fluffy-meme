"""Interchangeable per-tenant adapters for the Phase 2 comparison: tensor-train (TT), LoRA and VeRA.

Each target linear layer is wrapped once in a Slot. A Slot holds the frozen base layer and one adapter at a
time; set_method() swaps the adapter for every slot (for example to "lora" with r = 4) without reloading the
model. Every adapter's update starts at exactly zero, so the model with a fresh adapter equals the base model.

  tt    dW = c * TT(cores) with bond dimension r; c = 1/sqrt(r)            trainable: the TT cores
  lora  dW = c * B A,  A: r x in (Kaiming), B: out x r (zeros); c = 1/sqrt(r)   trainable: A, B
  vera  dW = diag(b) B_s diag(d) A_s with frozen random A_s (r x in_max) and B_s (out_max x r) shared by all
        layers (sliced to each layer's shape); d starts at 0.1, b at 0      trainable: d (r), b (out)

LoRA uses the rank-stabilized scale (Kalajdzievski 2023), the same 1/sqrt(r) factor as the TT adapter.
VeRA follows Kopiczko et al. (2024).

  quanta  QuanTA (Chen et al. 2024) with d axes ("quanta:4"): pairwise gates over a d-axis reshaping of the
        features, dW = C(W) - C(W0); see QuantaDelta                       trainable: the gates
"""
import itertools
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from tt import factorize, tt_to_matrix


class TTDelta(nn.Module):
    def __init__(self, out_f, in_f, r, device):
        super().__init__()
        d = len(out_f)
        ranks = [1] + [r] * (d - 1) + [1]
        cores = []
        for k in range(d):
            shape = (ranks[k], out_f[k], in_f[k], ranks[k + 1])
            g = torch.zeros(shape, device=device) if k == d - 1 else torch.randn(shape, device=device) / math.sqrt(ranks[k])
            cores.append(nn.Parameter(g))
        self.cores = nn.ParameterList(cores)
        self.c = 1.0 / math.sqrt(r)

    def matrix(self):
        return self.c * tt_to_matrix(list(self.cores))

    def forward(self, x):
        return F.linear(x, self.matrix().to(x.dtype))


class LoRADelta(nn.Module):
    def __init__(self, out_features, in_features, r, device):
        super().__init__()
        self.A = nn.Parameter(torch.empty(r, in_features, device=device))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))
        self.B = nn.Parameter(torch.zeros(out_features, r, device=device))
        self.c = 1.0 / math.sqrt(r)

    def matrix(self):
        return self.c * self.B @ self.A

    def forward(self, x):
        return self.c * F.linear(F.linear(x, self.A.to(x.dtype)), self.B.to(x.dtype))


class VeRADelta(nn.Module):
    def __init__(self, out_features, in_features, shared, device):
        super().__init__()
        self.shared = shared  # (A_s, B_s) frozen tensors, not parameters of this module
        r = shared[0].shape[0]
        self.out_features, self.in_features = out_features, in_features
        self.d = nn.Parameter(torch.full((r,), 0.1, device=device))
        self.b = nn.Parameter(torch.zeros(out_features, device=device))

    def matrix(self):
        a, b_s = self.shared[0][:, : self.in_features], self.shared[1][: self.out_features]
        return (self.b[:, None] * b_s) @ (self.d[:, None] * a)

    def forward(self, x):
        a, b_s = self.shared[0][:, : self.in_features], self.shared[1][: self.out_features]
        h = F.linear(x, a.to(x.dtype)) * self.d.to(x.dtype)
        return F.linear(h, b_s.to(x.dtype)) * self.b.to(x.dtype)


class QuantaDelta(nn.Module):
    """QuanTA (Chen et al., 2024), ported from the authors' code (github.com/quanta-fine-tuning/quanta,
    Apache-2.0), mode 'sum_opposite_freeze_one'.

    The input is padded to prod(n) features and reshaped to d axes n = factorize(max(out, in), d). One
    trainable "gate" acts on every pair of axes, applied in the authors' order; the output is cropped to `out`.
    dW = C(W) - C(W0), where C is that circuit of gates and W0 is a frozen copy of the initial gates (Kaiming
    uniform, as if each gate were a matrix). The authors merge -C(W0) into the base weight; the base weight is
    shared between tenants here, so the frozen circuit is evaluated instead. The update is the same.
    """

    def __init__(self, out_features, in_features, d, device):
        super().__init__()
        self.out_features, self.in_features = out_features, in_features
        self.n = factorize(max(out_features, in_features), d)
        self.total = math.prod(self.n)
        self.pairs = list(itertools.combinations(range(-1, -d - 1, -1), 2))
        ws = []
        for d1, d2 in self.pairs:
            n1, n2 = self.n[d1], self.n[d2]
            w = torch.empty(n2, n1, n2, n1, device=device)
            nn.init.kaiming_uniform_(w.view(n2 * n1, n2 * n1), a=math.sqrt(5), nonlinearity="linear")
            ws.append(nn.Parameter(w))
        self.w = nn.ParameterList(ws)
        self.register_buffer("w0", torch.cat([w.detach().flatten() for w in ws]))
        self.eqs = []
        for d1, d2 in self.pairs:  # x[..., axes]; contract axes d2, d1 with gate (out2, out1, in2, in1)
            ax = [chr(97 + k) for k in range(d)]
            o = ax.copy()
            o[d1], o[d2] = "Y", "Z"
            self.eqs.append(f"...{''.join(ax)},Z Y{ax[d2]}{ax[d1]}->...{''.join(o)}".replace(" ", ""))

    def frozen(self):
        out, k = [], 0
        for w in self.w:
            out.append(self.w0[k: k + w.numel()].view_as(w))
            k += w.numel()
        return out

    def circuit(self, x, gates):
        shape = x.shape[:-1]
        x = F.pad(x, (0, self.total - self.in_features)).reshape(-1, *self.n)
        for eq, g in zip(self.eqs, gates):
            x = torch.einsum(eq, x, g.to(x.dtype))
        return x.reshape(*shape, self.total)[..., : self.out_features]

    def forward(self, x):
        with torch.no_grad():
            y0 = self.circuit(x, self.frozen())
        return self.circuit(x, list(self.w)) - y0

    def matrix(self):
        eye = torch.eye(self.in_features, device=self.w0.device)
        return self.forward(eye).T


class Slot(nn.Module):
    """A frozen base linear layer plus one swappable adapter."""

    def __init__(self, base, d=4):
        super().__init__()
        self.base = base
        self.out_f, self.in_f = factorize(base.out_features, d), factorize(base.in_features, d)
        self.delta = None

    def forward(self, x):
        y = self.base(x)
        return y if self.delta is None else y + self.delta(x)


def add_slots(model, targets=("q_proj", "v_proj"), d=4):
    for p in model.parameters():
        p.requires_grad_(False)
    slots = {}
    for name, mod in list(model.named_modules()):
        for t in targets:
            lin = getattr(mod, t, None)
            if isinstance(lin, nn.Linear):
                s = Slot(lin, d=d)
                setattr(mod, t, s)
                slots[f"{name}.{t}" if name else t] = s
    if not slots:
        raise ValueError(f"no linear layers named {targets} found")
    return slots


def set_method(slots, method, r, seed=0):
    """Give every slot a fresh adapter of this method and size; returns the trainable parameters."""
    torch.manual_seed(seed)
    dev = next(iter(slots.values())).base.weight.device
    shared = None
    if method == "vera":
        out_max = max(s.base.out_features for s in slots.values())
        in_max = max(s.base.in_features for s in slots.values())
        g = torch.Generator(device="cpu").manual_seed(seed)
        a = torch.empty(r, in_max)
        b = torch.empty(out_max, r)
        nn.init.kaiming_uniform_(a, a=math.sqrt(5), generator=g)
        nn.init.kaiming_uniform_(b, a=math.sqrt(5), generator=g)
        shared = (a.to(dev), b.to(dev))
    for s in slots.values():
        o, i = s.base.out_features, s.base.in_features
        if method == "tt":
            s.delta = TTDelta(s.out_f, s.in_f, r, dev)
        elif method == "lora":
            s.delta = LoRADelta(o, i, r, dev)
        elif method == "vera":
            s.delta = VeRADelta(o, i, shared, dev)
        elif method == "quanta":
            s.delta = QuantaDelta(o, i, r, dev)
        elif method == "none":
            s.delta = None
        else:
            raise ValueError(f"unknown method {method}")
    return trainable(slots)


def trainable(slots):
    return [p for s in slots.values() if s.delta is not None for p in s.delta.parameters()]


def n_trainable(slots):
    return sum(p.numel() for p in trainable(slots))


def get_state(slots):
    return [p.detach().clone() for p in trainable(slots)]


@torch.no_grad()
def set_state(slots, state):
    for p, v in zip(trainable(slots), state):
        p.copy_(v)


def parse_config(c):
    """'lora:4' -> ('lora', 4)"""
    m, r = c.split(":")
    return m, int(r)
