"""Register FreeHawkes / SemHawkes as EasyTPP models so they train and are evaluated
by exactly the same pipeline (likelihood convention, thinning-based time/type prediction)
as NHP / THP.

EasyTPP convention: the first event of a sequence is only conditioned on; log-likelihood
covers events 2..N and the intervals [t_{i-1}, t_i] (num_events = N-1 per sequence).

SemHawkes reads (K, D) type-text embeddings from the .npy file named by $SEMHAWKES_EMB.
"""
import os

import numpy as np
import torch
from easy_tpp.model.basemodel import BaseModel

from .model import FreeHawkes, SemanticHawkes


class _HawkesMixin:
    def _make_core(self, K):
        raise NotImplementedError

    def __init__(self, model_config):
        super().__init__(model_config)
        self.K = self.num_event_types
        self.core = self._make_core(self.K).to(self.device)

    # ---- helpers --------------------------------------------------------
    def _prep(self, time_seqs, type_seqs, mask):
        # padded positions carry pad_token_id == K; map them to type 0 and rely on the mask
        types = torch.where(mask.bool(), type_seqs, torch.zeros_like(type_seqs))
        return time_seqs, types, mask.bool()

    def loglike_loss(self, batch=None, **kwargs):
        time_seqs, _, type_seqs, mask, _ = self.resolve_batch_inputs(batch, kwargs)
        t, types, m = self._prep(time_seqs, type_seqs, mask)
        mu, A, beta = self.core.params()
        L = t.shape[1]
        lower = torch.tril(torch.ones(L, L, dtype=torch.bool, device=t.device), diagonal=-1)  # i<j as [j,i]
        # pair tensors indexed [b, i(source), j(target)]
        a_src = A[types[:, :, None], types[:, None, :]]
        b_src = beta[types[:, :, None], types[:, None, :]]
        dt = (t[:, None, :] - t[:, :, None]).clamp(min=0)
        valid = lower.T[None] & m[:, :, None] & m[:, None, :]
        kern = torch.where(valid, a_src * b_src * torch.exp(-b_src * dt), torch.zeros_like(dt))
        lam_tgt = mu[types] + kern.sum(1)                                       # (B, L) intensity of true type
        tgt = m.clone(); tgt[:, 0] = False                                      # events 2..N
        event_ll = (torch.log(lam_tgt + 1e-9) * tgt).sum()
        t_last = torch.where(m, t, torch.full_like(t, -1e30)).max(1).values     # (B,)
        t0 = t[:, 0]
        remain = (t_last[:, None] - t).clamp(min=0)
        comp_ev = (A[types] * (1 - torch.exp(-beta[types] * remain[:, :, None]))).sum(-1)
        comp = mu.sum() * (t_last - t0) + (comp_ev * m).sum(1)
        n_events = int(tgt.sum().item())
        loss = -(event_ll - comp.sum())
        return loss, n_events

    def compute_intensities_at_sample_times(self, time_seqs, time_delta_seqs, type_seqs, sample_dtimes, **kwargs):
        """Intensities at t_i + d for every event i: (B, L, S, K). Exact, via per-pair decay states."""
        mask = (type_seqs != self.pad_token_id)
        t, types, m = self._prep(time_seqs, type_seqs, mask)
        mu, A, beta = self.core.params()
        B, L = t.shape
        K = self.K
        # state[b,a,k] = sum_{m<=i, a_m=a} exp(-beta[a,k] (t_i - t_m)), computed recursively
        state = torch.zeros(B, K, K, device=t.device)
        states = []
        prev_t = t[:, :1]
        for i in range(L):
            dt = (t[:, i:i + 1] - prev_t).clamp(min=0)                        # (B,1)
            state = state * torch.exp(-beta[None] * dt[:, :, None])
            onehot = torch.nn.functional.one_hot(types[:, i], K).float() * m[:, i:i + 1].float()  # (B,K)
            state = state + onehot[:, :, None]
            states.append(state)
            prev_t = t[:, i:i + 1]
        st = torch.stack(states, 1)                                            # (B,L,K,K)
        coef = st * (A * beta)[None, None]                                     # (B,L,K,K)
        S = sample_dtimes.shape[-1]
        out = torch.empty(B, L, S, K, device=t.device)
        step = 50
        for s0 in range(0, S, step):
            d = sample_dtimes[..., s0:s0 + step]                               # (B,L,s)
            decay = torch.exp(-beta[None, None, None] * d[..., None, None])    # (B,L,s,K,K)
            out[:, :, s0:s0 + step] = mu + (coef[:, :, None] * decay).sum(3)
        return out


# EasyTPP resolves `model_id` against the __name__ of *direct* BaseModel subclasses
class FreeHawkesTPP(_HawkesMixin, BaseModel):
    def _make_core(self, K):
        return FreeHawkes(K)


class SemHawkesTPP(_HawkesMixin, BaseModel):
    def _make_core(self, K):
        emb = np.load(os.environ["SEMHAWKES_EMB"])
        assert emb.shape[0] == K, (emb.shape, K)
        return SemanticHawkes(emb)
