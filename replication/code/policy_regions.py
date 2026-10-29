"""Table 4: firm policy regions at family-specific mu (R_copy = 0.57, R_transfer = 0.78, C_A = 0.05 C_N).

  python code/policy_regions.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataclasses import replace

from real_options import Params, act_region, gamma, v_star

R_COPY, R_TRANSFER = 0.57, 0.78
MU_HAT = {"Gemma": 1.15, "Phi": 1.31, "Llama": 1.67, "DeepSeek": 2.47, "Qwen": 2.54, "Mistral": 2.66}


def table():
    rows = []
    for fam, mu in MU_HAT.items():
        p = Params(mu=mu, C_A=0.05)
        reg = act_region(R_COPY, R_TRANSFER, p)
        rows.append((fam, mu, v_star(R_COPY, p), v_star(R_TRANSFER, p), reg, gamma(R_TRANSFER, R_COPY, p)))
    return rows


if __name__ == "__main__":
    print(f"{'family':<10}{'mu':>6}{'v*copy':>8}{'v*transfer':>11}   {'transfer-optimal band':<22}{'Gamma':>6}")
    for fam, mu, vc, vt, reg, G in table():
        band = f"{reg[0]:.2f} to {reg[1]:.2f}" if reg else "none"
        print(f"{fam:<10}{mu:>6.2f}{vc:>8.2f}{vt:>11.2f}   {band:<22}{G:>6.2f}")
