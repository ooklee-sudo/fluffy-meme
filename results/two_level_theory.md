# Theory vs numerics: share of the flat-price loss recovered by a G-level schedule

Azure 2024 hour-of-day profile (24 equally likely phases), c = 77, quasi-static. 'quad' = prediction from the quadratic (local) theory with weights pi_k omega_k; 'exact' = dynamic programme over contiguous groups on the full welfare curves.

| P | unpriced / capacity | c0/P | omega range | lower bound (MAD/sd)^2 | G=2 quad | G=2 exact | G=3 quad / exact | G=4 quad / exact | G=6 quad / exact |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 1.4 | 0.0 | 1.293-173.294 | 0.47 | 0.76 | 0.69 | 0.89 / 0.85 | 0.97 / 0.94 | 0.99 / 0.98 |
| 20 | 1.4 | 0.15 | 1.521-189.399 | 0.47 | 0.76 | 0.69 | 0.89 / 0.85 | 0.97 / 0.94 | 0.99 / 0.98 |
| 10 | 1.2 | 0.0 | 2.217-223.787 | 0.48 | 0.77 | 0.72 | 0.90 / 0.84 | 0.97 / 0.96 | 0.99 / 0.99 |
| 40 | 2.0 | 0.0 | 0.924-147.472 | 0.61 | 0.78 | 0.65 | 0.91 / 0.79 | 0.94 / 0.87 | 0.98 / 0.95 |
