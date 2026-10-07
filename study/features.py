"""Event counting and Poisson-Score. Events are counted per fixed 500-token window."""
import re, numpy as np
from scipy import stats

WIN = 500
TOK = re.compile(r"\S+")
MARKERS = ["furthermore", "moreover", "therefore", "in contrast", "crucially", "additionally", "however",
           "consequently", "thus", "notably", "in addition", "overall", "specifically", "importantly"]
MARK_RE = re.compile(r"\b(" + "|".join(MARKERS) + r")\b", re.I)
PASSIVE = re.compile(r"\b(?:is|are|was|were|been|being|be)\s+(?:\w+ly\s+)?(?:\w+ed|\w+en|shown|made|found|given|known|seen|done|built|taken)\b", re.I)
NOMINAL = re.compile(r"\b\w{3,}(?:tion|tions|ment|ments|ity|ities)\b", re.I)
FEATURES = {
    "parentheses": lambda s: s.count("(") ,
    "brackets": lambda s: s.count("["),
    "semicolons": lambda s: s.count(";"),
    "quotes": lambda s: len(re.findall(r'["“”]', s)) // 2,
    "markers": lambda s: len(MARK_RE.findall(s)),
    "passive": lambda s: len(PASSIVE.findall(s)),
    "nominal": lambda s: len(NOMINAL.findall(s)),
}
NAMES = list(FEATURES)

def windows(text):
    toks = TOK.findall(text)
    return [" ".join(toks[i:i + WIN]) for i in range(0, len(toks) - WIN + 1, WIN)]

def counts(text):
    """matrix (n_windows, n_features) of event counts"""
    w = windows(text)
    return np.array([[f(s) for f in FEATURES.values()] for s in w], dtype=float).reshape(len(w), len(NAMES))

def doc_stats(C):
    """per-feature rate, dispersion index (var/mean), and Poisson chi-square GoF p-value"""
    n = C.shape[0]
    mean = C.mean(0); var = C.var(0, ddof=1) if n > 1 else np.zeros(C.shape[1])
    di = np.where(mean > 0, var / np.maximum(mean, 1e-9), np.nan)
    chi = np.where(mean > 0, (n - 1) * di, np.nan)           # Poisson dispersion test
    p = np.where(mean > 0, stats.chi2.sf(chi, n - 1), np.nan)  # upper tail: over-dispersion
    plo = np.where(mean > 0, stats.chi2.cdf(chi, n - 1), np.nan)  # lower tail: under-dispersion
    return mean, di, p, plo

class PoissonScore:
    """Reference built on human text only. Per-feature deviation = |z| of (log rate, log dispersion index)
    against the human distribution; the score maps mean deviation into [0,1)."""
    def fit(self, stat_list):
        M = np.array([np.log1p(s[0]) for s in stat_list]); D = np.array([np.log(np.clip(np.nan_to_num(s[1], nan=1.0), 0.05, None)) for s in stat_list])
        self.mu_r, self.sd_r = M.mean(0), M.std(0) + 1e-6
        self.mu_d, self.sd_d = D.mean(0), D.std(0) + 1e-6
        return self
    def components(self, s):
        zr = (np.log1p(s[0]) - self.mu_r) / self.sd_r
        zd = (np.log(np.clip(np.nan_to_num(s[1], nan=1.0), 0.05, None)) - self.mu_d) / self.sd_d
        return np.concatenate([zr, zd])
    def score(self, s):
        z = np.abs(self.components(s))
        return float(1 - np.exp(-z.mean() / 2))
