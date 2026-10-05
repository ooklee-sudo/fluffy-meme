# Tables transcribed from `unlearn_audit_exp.py --stage analyze` (RunPod, seed 0, Qwen2.5-0.5B, 4 training formats)

Transcribed by hand from terminal output pasted into the session; the JSON files (`retrain.json`, `unlearn.json`,
`conceal.json`, `conceal_heldout.json`) stay on the pod and were not committed. Treat these numbers as unaudited copies.

```
exact Shapley (both): [0.2055 0.2077 0.2003 0.204 ]  sum=0.8175  v(N)=0.8175
leave-one-out: [0.2071 0.208  0.2089 0.2051]
relearn control (retrained empty): 0.114 -> 0.151

 s  eps(0)   rho(0)  kappa(0)  L1(phi(eps))  L1(seq-set)  relearn 0->5
  8 +0.732 +0.730  -0.003   0.730      0.009       0.837->0.881
 12 +0.624 +0.620  -0.004   0.620      0.037       0.728->0.866
 16 +0.454 +0.449  -0.005   0.449      0.081       0.559->0.850
 20 +0.255 +0.251  -0.004   0.251      0.128       0.362->0.823
 24 +0.084 +0.083  -0.001   0.087      0.152       0.195->0.814
 28 -0.023 -0.021  +0.003   0.076      0.182       0.091->0.804   (extra run)
 32 -0.107 -0.099  +0.008   0.104      0.172       0.011->0.753
 40 -0.121 -0.111  +0.010   0.113      0.159       0.000->0.412   (extra run)
 48 -0.121 -0.111  +0.010   0.111      0.288       0.000->0.400   (extra run)
```

Retrain log (author score by coalition): empty 0.111, full 0.929.

conceal.json (format design: audit = formats 2,3 of the same questions)
```
 s  b  public  secret   gap   post-relearn(secret)
 16  0 0.560  0.564  +0.004  0.850
 16  1 0.449  0.454  +0.005  0.840
 16  2 0.237  0.242  +0.006  0.804
 16  4 0.096  0.100  +0.004  0.754
 16  8 0.053  0.056  +0.003  0.731
 20  0 0.362  0.366  +0.005  0.824
 20  1 0.281  0.286  +0.005  0.813
 20  2 0.125  0.129  +0.005  0.767
 20  4 0.041  0.044  +0.002  0.726
 20  8 0.020  0.022  +0.001  0.697
 24  0 0.194  0.198  +0.004  0.815
 24  1 0.142  0.146  +0.004  0.793
 24  2 0.049  0.052  +0.004  0.733
 24  4 0.013  0.014  +0.001  0.685
 24  8 0.005  0.006  +0.000  0.662
```

conceal_heldout.json (held-out design: developer tunes on half of the forgotten questions, audit asks the other half)
```
 s  b  public  secret   gap   post-relearn(secret)
 16  0 0.618  0.691  +0.074  0.849
 16  1 0.516  0.572  +0.056  0.841
 16  2 0.293  0.332  +0.040  0.814
 16  4 0.125  0.145  +0.021  0.754
 16  8 0.070  0.083  +0.013  0.738
 16 16 0.063  0.074  +0.012  0.733
 20  0 0.450  0.504  +0.054  0.822
 20  1 0.373  0.412  +0.038  0.812
 20  2 0.195  0.218  +0.023  0.785
 20  4 0.074  0.084  +0.010  0.735
 20  8 0.038  0.044  +0.006  0.716
 20 16 0.033  0.039  +0.005  0.711
 24  0 0.280  0.292  +0.012  0.803
 24  1 0.224  0.229  +0.005  0.793
 24  2 0.100  0.103  +0.003  0.755
 24  4 0.032  0.033  +0.001  0.721
 24  8 0.015  0.015  +0.000  0.694
 24 16 0.013  0.013  +0.000  0.689
```
