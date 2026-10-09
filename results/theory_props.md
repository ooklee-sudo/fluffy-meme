# Propositions (numerical verification) and strategic extensions

## Code trace (c=7)

### Propositions

- P1 first-best rate and toll strictly increasing in demand potential: **True**; Lam -> t(lam*(Lam)) convex on [0.3c, 3c]: **False**
- P2 derivative identity dW/dp = -sum pi kappa (p - t): p=1: numeric 0.223 vs formula 0.223; p=3: numeric -0.297 vs formula -0.297; p=6: numeric -1.045 vs formula -1.045; p=9: numeric -1.774 vs formula -1.774
- P2 phase tolls at first best: [16.53, 0.54]; optimal flat price 1.85 (inside [0.54, 16.53]: True)
- P3 exact loss: direct 4.8265 vs integral formula 4.8264
- P4 burst-blind price (first-best toll at mean potential) 6.06 vs kappa-weighted optimum flat 1.85 vs mean of phase tolls 1.34 -> blind price is above the optimal flat price

### Strategic extensions

- Code trace (c=7): heterogeneous delay costs (v = 0.5 / 2, 50:50): phase-dependent welfare 46.66 (prices 16.0, 0.6), best flat 41.90 (p=1.9), flat loss 10.2%
- Code trace (c=7): duopoly Nash flat price 2.8: profit/firm 11.78, welfare 94.36; phase prices 17.7, 2.5: profit/firm 14.38, welfare 92.67
