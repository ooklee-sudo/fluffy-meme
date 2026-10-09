"""Semantic Hawkes: multivariate Hawkes process whose parameters are functions
of LLM text embeddings of the event-type descriptions.

    lambda_k(t) = mu_k + sum_{t_i < t} A[a_i,k] * beta[a_i,k] * exp(-beta[a_i,k] (t - t_i))

* A[i,k] >= 0 is the branching ratio ("how strongly type i triggers type k"),
  so the Hawkes structure stays interpretable and non-inhibitory.
* Exponential kernels give an exact closed-form compensator, so the
  log-likelihood needs no Monte-Carlo integration (unlike TPP-LLM / Language-TPP).
* `SemanticHawkes`: A, beta, mu = f(text embeddings)   (proposed)
* `FreeHawkes`:     A, beta, mu are free parameters    (classical MHP baseline)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

MIN_BETA = 0.05
# Upper bound on the decay rate (event times are in units of the mean inter-event time). Without it, tied timestamps
# (identical times, e.g. same-day reviews) let beta -> infinity inflate the likelihood without modelling any dynamics.
MAX_BETA = 20.0


class _Base(nn.Module):
    def params(self):  # -> mu (K,), A (K,K), beta (K,K)
        raise NotImplementedError

    def excitation(self):
        return self.params()[1].detach()

    def _pair_terms(self, times, types, mask):
        mu, A, beta = self.params()
        a_src = A[types[:, :, None], types[:, None, :]]      # (B,L,L) source i -> target j
        b_src = beta[types[:, :, None], types[:, None, :]]
        dt = times[:, None, :] - times[:, :, None]            # t_j - t_i
        valid = (dt > 0) & mask[:, :, None] & mask[:, None, :]
        return mu, A, beta, a_src, b_src, dt, valid

    def log_likelihood(self, times, types, mask, horizon):
        """Per-sequence exact log-likelihood (B,)."""
        mu, A, beta, a_src, b_src, dt, valid = self._pair_terms(times, types, mask)
        kern = torch.where(valid, a_src * b_src * torch.exp(-b_src * dt.clamp(min=0)),
                           torch.zeros_like(dt))
        lam = mu[types] + kern.sum(1)                          # intensity of the observed type at t_j
        log_term = (torch.log(lam + 1e-9) * mask).sum(1)
        # compensator: integral of sum_k lambda_k over [0, H]
        remain = (horizon[:, None] - times).clamp(min=0)       # H - t_i
        comp_ev = (A[types] * (1 - torch.exp(-beta[types] * remain[:, :, None]))).sum(-1)
        comp = mu.sum() * horizon + (comp_ev * mask).sum(1)
        return log_term - comp

    @torch.no_grad()
    def next_type_accuracy(self, times, types, mask):
        """argmax_k lambda_k(t_j) vs true type, for j >= 1 (time given, as in EasyTPP)."""
        mu, A, beta, a_src, b_src, dt, valid = self._pair_terms(times, types, mask)
        K = mu.numel()
        # full intensity of every type k at each event time: (B,L,K)
        A_s, b_s = A[types], beta[types]                       # (B,L,K) by source event
        kern = A_s[:, :, None, :] * b_s[:, :, None, :] * torch.exp(
            -b_s[:, :, None, :] * dt.clamp(min=0)[:, :, :, None])
        lam = mu + (kern * valid[..., None]).sum(1)            # (B,L,K)
        pred = lam.argmax(-1)
        keep = mask.clone()
        keep[:, 0] = False
        return ((pred == types) & keep).sum().item(), keep.sum().item()


class FreeHawkes(_Base):
    def __init__(self, K):
        super().__init__()
        self.mu_raw = nn.Parameter(torch.full((K,), -2.0))
        self.A_raw = nn.Parameter(torch.full((K, K), -2.0))
        self.b_raw = nn.Parameter(torch.zeros(K, K))

    def params(self):
        return (F.softplus(self.mu_raw), F.softplus(self.A_raw),
                (F.softplus(self.b_raw) + MIN_BETA).clamp(max=MAX_BETA))


class SemanticHawkes(_Base):
    """Parameters are bilinear/MLP functions of frozen text embeddings (K, D)."""

    def __init__(self, embeddings, hidden=32):
        super().__init__()
        self.register_buffer("emb", torch.as_tensor(embeddings, dtype=torch.float32))
        D = self.emb.shape[1]
        self.enc = nn.Sequential(nn.Linear(D, hidden), nn.Tanh(), nn.Linear(hidden, hidden))
        self.src_A, self.dst_A = nn.Linear(hidden, hidden, bias=False), nn.Linear(hidden, hidden, bias=False)
        self.src_b, self.dst_b = nn.Linear(hidden, hidden, bias=False), nn.Linear(hidden, hidden, bias=False)
        self.mu_head = nn.Linear(hidden, 1)
        self.bias_A = nn.Parameter(torch.tensor(-2.0))
        self.bias_b = nn.Parameter(torch.tensor(0.0))
        self.scale = hidden ** -0.5

    def params(self):
        h = self.enc(self.emb)                                 # (K,H)
        A = F.softplus(self.src_A(h) @ self.dst_A(h).T * self.scale + self.bias_A)
        beta = (F.softplus(self.src_b(h) @ self.dst_b(h).T * self.scale + self.bias_b) + MIN_BETA).clamp(max=MAX_BETA)
        mu = F.softplus(self.mu_head(h).squeeze(-1) - 2.0)
        return mu, A, beta
