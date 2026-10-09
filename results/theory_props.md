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

## Conversation trace (c=45)

### Propositions

- P1 first-best rate and toll strictly increasing in demand potential: **True**; Lam -> t(lam*(Lam)) convex on [0.3c, 3c]: **False**
- P2 derivative identity dW/dp = -sum pi kappa (p - t): p=1: numeric 34.752 vs formula 34.752; p=3: numeric 24.776 vs formula 24.776; p=6: numeric 3.451 vs formula 3.451; p=9: numeric -23.610 vs formula -23.610
- P2 phase tolls at first best: [1.19, 3.15, 4.93, 6.52, 8.63]; optimal flat price 6.38 (inside [1.19, 8.63]: True)
- P3 exact loss: direct 31.8094 vs integral formula 31.8093
- P4 burst-blind price (first-best toll at mean potential) 5.36 vs kappa-weighted optimum flat 6.38 vs mean of phase tolls 4.95 -> blind price is below the optimal flat price

### Strategic extensions

- Conversation trace (c=45): heterogeneous delay costs (v = 0.5 / 2, 50:50): phase-dependent welfare 487.03 (prices 1.2, 3.0, 4.8, 6.3, 8.4), best flat 458.57 (p=6.1), flat loss 5.8%
- Conversation trace (c=45): duopoly Nash flat price 5.4: profit/firm 209.06, welfare 972.04; phase prices 4.5, 5.8, 8.0, 7.6, 9.8: profit/firm 276.96, welfare 968.99
