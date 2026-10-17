"""Prompt-wording robustness (stage 5): counts hand-transcribed from analyze_ci.py / hillstrom_rd.py output for
4 models x 2 prompts, wordings 'third' and 'survey'. Order of cells: haiku plain, haiku anchor, sonnet plain, sonnet anchor,
llama plain, llama anchor, gpt-4o-mini plain, gpt-4o-mini anchor. None = ratio undefined."""
import numpy as np
REF = {"retail": 2.49, "grocery": 7.85}
AB = {  # variance-to-mean point estimates of designs A and B
 ("retail", "third"): [.32, .26, .90, None, .35, .98, .17, .01, 1.10, 1.00, 2.48, None, 1.71, .99, .23, .12],
 ("retail", "survey"): [.17, .23, .41, .61, .25, None, .06, .47, 2.99, 1.23, 1.81, None, 1.14, .98, .33, .96],
 ("grocery", "third"): [.28, .07, .11, .00, .36, .33, .36, .03, .14, .17, .08, .04, .18, .27, .12, .04],
 ("grocery", "survey"): [15.68, 2.58, .07, .18, .01, .12, .05, .02, .10, .09, .26, .03, .21, .06, .03, .10]}
# design D: variance-to-mean estimate, and whether the interval contains the reference
D_VMR = {("retail", "third"): [1, 1, 0, 0, 1, 1, 0, 1], ("retail", "survey"): [0, 1, 1, 0, 0, 0, 1, 0],
         ("grocery", "third"): [1, 1, 1, 1, 0, 1, 1, 1], ("grocery", "survey"): [0, 1, 1, 1, 1, 0, 0, 1]}
D_MEAN = {("retail", "third"): [0, 1, 1, 1, 1, 0, 0, 0], ("retail", "survey"): [1, 1, 1, 0, 0, 0, 0, 1],
          ("grocery", "third"): [0, 1, 1, 1, 0, 1, 1, 1], ("grocery", "survey"): [0, 1, 1, 1, 1, 0, 0, 1]}
C_ZERO_BELOW = {("retail", "third"): [1, 0, 1, 1, 1, 1, 1, 0], ("retail", "survey"): [1, 0, 1, 1, 1, 1, 1, 1],
                ("grocery", "third"): [1, 0, 1, 1, 1, 1, 1, 1], ("grocery", "survey"): [1] * 8}
# email, design C_prob: simulated men's absolute lift over the real one, by outcome; RD signs (men, women)
EM = {"third": dict(visit=[2.0, -.1, .5, 1.6, .5, 1.2, 0.0, 1.6], purchase=[6.2, -.2, 5.3, 6.0, 15.6, 18.4, 3.1, 17.3],
                    gap_visit=[-.008, -.005, -.008, -.004, .002, .024, 0, -.008], gap_purchase=[-.008, -.007, .006, -.004, -.005, .013, -.002, -.010],
                    sign_ok_visit=6, sign_ok_purchase=7),
      "survey": dict(visit=[2.2, .2, 1.5, 1.7, 3.6, 1.2, 2.2, 1.8], purchase=[22.8, 5.6, 5.3, 9.2, 58.6, 18.0, 25.1, 17.1],
                     gap_visit=[-.020, -.003, -.010, -.006, -.005, .020, -.020, -.027], gap_purchase=[-.015, .009, -.004, -.018, .015, .020, .005, -.023],
                     sign_ok_visit=8, sign_ok_purchase=8)}
for k, v in AB.items():
    d = [x for x in v if x is not None]; print(k, "A/B below ref", sum(x < REF[k[0]] for x in d), "of", len(d))
for name, T in (("D VMR match", D_VMR), ("D mean match", D_MEAN), ("C zero below", C_ZERO_BELOW)):
    print(name, {k: sum(v) for k, v in T.items()}, "total", sum(sum(v) for v in T.values()), "of", 8 * len(T))
for w, e in EM.items():
    v, p = np.array(e["visit"]), np.array(e["purchase"])
    print(w, "visit within 0.5-2:", int(((v >= .5) & (v <= 2.0)).sum()), "above 2:", int((v > 2.0).sum()), "below .5:", int((v < .5).sum()),
          "| purchase above 2:", int((p > 2).sum()), "above 5:", int((p > 5).sum()), "median", np.median(p), "| gap positive", int((np.array(e["gap_visit"]) > 0).sum() + (np.array(e["gap_purchase"]) > 0).sum()), "of 16")
