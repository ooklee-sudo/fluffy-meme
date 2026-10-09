"""Synthetic text-annotated multivariate Hawkes data.

Event types carry short text descriptions drawn from a few semantic topics.
The ground-truth excitation matrix depends on topics (same-topic types excite
each other, plus a few cross-topic links), so a model that reads the text can
in principle recover the structure with far less data than a free K x K matrix.
"""
import numpy as np

TOPICS = {
    "server": ["server", "outage", "restart", "timeout", "latency", "crash"],
    "payment": ["payment", "refund", "invoice", "card", "declined", "chargeback"],
    "login": ["login", "password", "reset", "account", "locked", "token"],
    "shipping": ["shipping", "parcel", "delay", "warehouse", "courier", "lost"],
}


def make_event_types(k_per_topic=3, seed=0):
    """Return (descriptions, topic_ids) for K = 4 * k_per_topic event types."""
    rng = np.random.default_rng(seed)
    descs, topic_ids = [], []
    for t, (name, words) in enumerate(TOPICS.items()):
        for _ in range(k_per_topic):
            w = rng.choice(words[1:], size=2, replace=False)
            descs.append(f"{name} {w[0]} {w[1]}")
            topic_ids.append(t)
    return descs, np.array(topic_ids)


def make_true_params(topic_ids, seed=0, same=0.35, cross=0.15, n_cross=3, beta=1.5):
    """Topic-structured excitation A (K x K), decay beta, base rate mu."""
    rng = np.random.default_rng(seed)
    K = len(topic_ids)
    A = np.where(topic_ids[:, None] == topic_ids[None, :], same, 0.0)
    A *= rng.uniform(0.6, 1.4, size=(K, K))
    for _ in range(n_cross):  # a few cross-topic causal links
        i, j = rng.choice(K, size=2, replace=False)
        if topic_ids[i] != topic_ids[j]:
            A[i, j] = cross
    # A[i, j]: excitation of type j caused by a past event of type i (integrated mass)
    rho = np.max(np.abs(np.linalg.eigvals(A)))
    if rho > 0.7:
        A *= 0.7 / rho
    mu = rng.uniform(0.05, 0.15, size=K)
    return mu, A, np.full((K, K), beta)


def simulate(mu, A, beta, T, rng):
    """Ogata thinning for a multivariate Hawkes process with exp kernels.

    lambda_j(t) = mu_j + sum_i A[i,j] * beta[i,j] * exp(-beta[i,j] (t - t_i))
    so A[i,j] is the branching ratio (expected # of j-children of an i-event).
    """
    K = len(mu)
    times, types = [], []

    def intensity(t):
        lam = mu.copy()
        for ti, ki in zip(times, types):
            lam += A[ki] * beta[ki] * np.exp(-beta[ki] * (t - ti))
        return lam

    t = 0.0
    while True:
        lam_bar = intensity(t).sum()  # intensity only decays until next event
        t += rng.exponential(1.0 / lam_bar)
        if t >= T:
            break
        lam = intensity(t)
        if rng.uniform() * lam_bar <= lam.sum():
            k = rng.choice(K, p=lam / lam.sum())
            times.append(t)
            types.append(k)
    return np.array(times), np.array(types, dtype=np.int64)


def make_dataset(n_seq, T, mu, A, beta, seed=0, max_len=64):
    rng = np.random.default_rng(seed)
    seqs = []
    while len(seqs) < n_seq:
        t, k = simulate(mu, A, beta, T, rng)
        if len(t) >= 3:
            # truncated sequences are observed only up to their last kept event
            h = T if len(t) <= max_len else float(t[max_len - 1])
            seqs.append((t[:max_len], k[:max_len], h))
    return seqs


def collate(seqs):
    """Pad to a batch: times (B,L), types (B,L), mask (B,L), horizon (B,)."""
    import torch
    B = len(seqs)
    L = max(len(s[0]) for s in seqs)
    times = torch.zeros(B, L)
    types = torch.zeros(B, L, dtype=torch.long)
    mask = torch.zeros(B, L, dtype=torch.bool)
    horizon = torch.zeros(B)
    for b, (t, k, h) in enumerate(seqs):
        n = len(t)
        times[b, :n] = torch.as_tensor(t, dtype=torch.float32)
        types[b, :n] = torch.as_tensor(k)
        mask[b, :n] = True
        horizon[b] = h
    return times, types, mask, horizon
