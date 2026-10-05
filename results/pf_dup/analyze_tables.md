# Duplication run (P3): `--dup 1 2 4 8`, seed 0 composition, s in {8, 20, 28, 32}
Transcribed from the terminal output of `unlearn_audit_exp.py --stage analyze --out /workspace/results/dup` (RunPod). Unaudited copy.

```
exact Shapley (both): [0.2082 0.2212 0.2122 0.2153]  sum=0.8570  v(N)=0.8570
leave-one-out: [0.2114 0.2245 0.2132 0.2142]
relearn control (retrained empty): 0.114 -> 0.151

 s  eps(0)   rho(0)  kappa(0)  L1(phi(eps))  L1(seq-set)  relearn 0->5
  8 +0.823 +0.827  +0.004   0.827      0.004       0.934->0.937
 20 +0.742 +0.746  +0.005   0.746      0.011       0.850->0.890
 28 +0.615 +0.620  +0.006   0.620      0.086       0.722->0.862
 32 +0.487 +0.494  +0.006   0.494      0.155       0.596->0.847

Per-group bias vs duplication factor k (author component; phi_i(eps) < 0 means undervalued)
 s=8  [k=1: phi=0.210 bias=-0.198 rel=-0.94]  [k=2: phi=0.220 bias=-0.211 rel=-0.96]  [k=4: phi=0.214 bias=-0.207 rel=-0.97]  [k=8: phi=0.218 bias=-0.211 rel=-0.97]
 s=20 [k=1: phi=0.210 bias=-0.172 rel=-0.82]  [k=2: phi=0.220 bias=-0.192 rel=-0.87]  [k=4: phi=0.214 bias=-0.188 rel=-0.88]  [k=8: phi=0.218 bias=-0.194 rel=-0.89]
 s=28 [k=1: phi=0.210 bias=-0.135 rel=-0.64]  [k=2: phi=0.220 bias=-0.164 rel=-0.75]  [k=4: phi=0.214 bias=-0.156 rel=-0.73]  [k=8: phi=0.218 bias=-0.165 rel=-0.76]
 s=32 [k=1: phi=0.210 bias=-0.099 rel=-0.47]  [k=2: phi=0.220 bias=-0.143 rel=-0.65]  [k=4: phi=0.214 bias=-0.121 rel=-0.57]  [k=8: phi=0.218 bias=-0.130 rel=-0.60]
```
