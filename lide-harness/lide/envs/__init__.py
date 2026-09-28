from .coding import CodingEnv
from .ops import OpsEnv

ENVIRONMENTS = {"coding": CodingEnv, "ops": OpsEnv}


def make_env(name: str, **kw):
    if name not in ENVIRONMENTS:
        raise ValueError(f"Unknown environment '{name}'. Options: {sorted(ENVIRONMENTS)}")
    return ENVIRONMENTS[name](**kw)
