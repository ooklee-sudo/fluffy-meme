---
title: "Strategic Evasion and the Design of Screens for Machine-Written Scholarly Text"
subtitle: "Supplementary analytical model with an adversarial test (exploratory)"
---

# 1. Purpose and status

The cascade model treats authors as passive: machine papers have fixed characteristics, and the organization chooses how deeply to screen. Real authors can adapt, and a screen whose features are known may lose its power. This note adds a strategic layer. It sets out a simple model in which a machine-using author chooses how hard to evade the screen, and it calibrates the model with an adversarial experiment on our data. Both parts are exploratory. The evasion experiment is a crude, automated attack, so it gives a lower bound on what an adaptive attacker could do, and the cost of evasion is not measured.

# 2. Model

A machine-using author chooses an evasion effort e in [0, 1]. Effort is costly, at (κ/2)e², and it lowers the probability that the paper is detected to d(e), with d(0) = d₀ the detection rate against a non-adaptive author. If the paper passes, the author gains B; if it is detected, the author loses P. The author's payoff is u(e) = B(1 − d(e)) − P·d(e) − (κ/2)e². Let m = (B + P)/κ be the ratio of what is at stake to the cost of effort. The author then chooses e to minimize m·d(e) + e²/2. The organization, which anticipates this, cares about the detection rate d(e*) that remains in equilibrium, not d₀.

**Proposition 5 (evasion rises with the stakes).** If d is differentiable and decreasing, the optimal effort e* satisfies m·|d′(e*)| = e*, or e* = 1 at the corner. Effort is therefore nondecreasing in m and in the steepness of d, so equilibrium detection d(e*) falls as stakes rise or evasion becomes cheaper.

**Proposition 6 (the detectability paradox).** If d(e) = d₀(1 − e), then e* = min(1, m·d₀) and d(e*) = d₀(1 − m·d₀) whenever m·d₀ ≤ 1. Equilibrium detection is maximized at d₀ = 1/(2m), where it equals 1/(4m), and *decreases* in d₀ beyond that point. A screen that is very effective against non-adaptive authors provokes more evasion, and past a point it ends up detecting less than a weaker screen would.

*Proof.* The first-order condition gives m·d₀ = e. Substituting gives d₀(1 − m·d₀), whose derivative in d₀ is 1 − 2m·d₀. ∎

**Proposition 7 (robust design).** Let a screen be built from two feature sets with detection curves d_A(e) and d_B(e), where d_B is flat in e because those features cannot be cheaply edited. If d_B(0) < d_A(0) but d_A falls steeply, there is a threshold m̂ such that the screen based on B has higher equilibrium detection for all m > m̂. The organization should prefer features that are costly to manipulate even at some cost in raw accuracy.

# 3. Adversarial experiment

We built a white-box attack on the five events that are easy to edit: parentheses, square brackets, semicolons, quotation marks, and discourse markers. For each machine paper, the attack moves a share e of the way from the paper's own count to the human mean count for each event, and places the edits in two of the four windows, as human text clusters. Passives and nominalizations are not edited. The attack knows the features but not the detector's weights. The detector (clustering features) is trained on human papers and the other two generators using clean text, and attacked texts are only scored. Edits are programmatic and crude, so the text is not natural, and a judge or a human reader would likely notice that.

| Target | e = 0 | e = 0.25 | e = 0.5 | e = 0.75 | e = 1 |
|:--|:--|:--|:--|:--|:--|
| GPT-4o | 0.959 / 0.73 | 0.888 / 0.33 | 0.849 / 0.24 | 0.824 / 0.12 | 0.800 / 0.10 |
| Claude | 0.777 / 0.18 | 0.634 / 0.05 | 0.539 / 0.02 | 0.473 / 0.01 | 0.471 / 0.01 |
| Llama | 0.932 / 0.69 | 0.852 / 0.37 | 0.799 / 0.20 | 0.763 / 0.17 | 0.721 / 0.12 |
| Mixture | 0.889 / 0.53 | 0.791 / 0.25 | 0.729 / 0.15 | 0.687 / 0.10 | 0.664 / 0.08 |

: Table 1. AUC / share of machine papers detected at a 5% false-positive rate, by evasion effort e.

The screen degrades quickly. Averaged over generators, the AUC falls from 0.889 to 0.664 and the share detected at a 5% false-positive rate falls from 53% to 8% under full attack. Half of the loss occurs at e = 0.25, so the first edits are the most effective, which makes d(e) steep near zero and, by Proposition 5, pushes equilibrium effort up. For Claude papers the AUC falls below 0.5, so edited Claude papers look *more* human than real human papers.

Table 2 separates the features. A detector built only on the two unedited events (passives and nominalizations) is unaffected by the attack, with a mixture AUC of 0.780 before and 0.779 after, whereas a detector built only on the five edited events falls from 0.849 to 0.491, which is chance. The robust features are weaker without an attack (mixture AUC 0.780 against 0.889 for all seven events), and weak for Claude papers (0.65).

| Feature set | Target | e = 0: AUC / detected | e = 1: AUC / detected |
|:--|:--|:--|:--|
| Passive and nominalization only | Mixture | 0.780 / 0.34 | 0.779 / 0.33 |
| Five edited events only | Mixture | 0.849 / 0.35 | 0.491 / 0.00 |
| All seven events | Mixture | 0.889 / 0.53 | 0.664 / 0.08 |

: Table 2. Detection by feature set, mixture of generators.

# 4. Equilibrium

Table 3 uses the measured mixture detection curve (53% falling to 8%) in the author's problem for a range of m, and compares the full screen with a screen built on the hard-to-edit events, whose detection is nearly flat (34% to 33%).

| m = (B + P)/κ | Full screen: e* | Full screen: detection | Hard-to-edit only: e* | Hard-to-edit only: detection |
|--:|--:|--:|--:|--:|
| 0.10 | 0.11 | 0.41 | 0.00 | 0.34 |
| 0.25 | 0.25 | 0.25 | 0.01 | 0.34 |
| 0.50 | 0.25 | 0.25 | 0.02 | 0.34 |
| 1.00 | 0.41 | 0.19 | 0.04 | 0.34 |
| 2.00 | 0.50 | 0.15 | 0.08 | 0.34 |
| 4.00 | 0.75 | 0.10 | 0.16 | 0.33 |

: Table 3. Equilibrium evasion effort and the detection rate that remains (share detected at a 5% false-positive rate), by the ratio of stakes to evasion cost.

Once evasion is not very costly relative to the stakes (m of about 0.2 or more), the full screen's equilibrium detection falls below that of the hard-to-edit screen (the crossover is at m ≈ 0.16). At m = 1, the full screen is expected to detect 19% of machine papers against 34% for the hard-to-edit design, although the full screen detects 53% of papers from non-adaptive authors. This is the detectability paradox in numbers.

# 5. Implications

First, accuracy measured against non-adaptive authors overstates the value of a screen whose features are public. Because our own results are published, the relevant benchmark is the equilibrium detection rate and not the headline AUC. Second, the design lesson is to build screens from features that are costly to manipulate, even if they are weaker on non-adaptive text. In our data these are passives and nominalizations, which are harder to edit with simple tools than punctuation. Third, secrecy is a weak defense, since methods get published and reverse-engineered, so rotating or ensembling features is a more credible one. Fourth, the judges' behavior under this kind of attack is unknown; the edits here may well be noticeable to a language-model judge, and a judge could be more robust or less so than the screen.

# 6. Limitations

The attack is crude and programmatic. It is a lower bound on a real adaptive attacker, who could paraphrase text with a language model, edit passives and nominalizations too, or optimize against the detector's weights. We chose the hard-to-edit feature set *because* our attack left it untouched, so its robustness is conditional on the attack and has not been tested against an attack that targets it. The cost of evasion (κ) and the stakes (B and P) are not measured, so we report equilibrium results as functions of their ratio. The model has a single decision by a single author, takes the base rate π as given (it does not let authors decide whether to use a model at all), and ignores the cost of editing text so that it reads naturally. The detector used in the attack is the one trained for the cross-generator analyses, and we did not test whether retraining on attacked text would restore detection. The judges were not attacked.
