> **SUPERSEDED.** This framing note predates the real model-pair results (ACT did not beat copy). See
> `manuscript/ijoc_manuscript.tex` for the current abstract, introduction and claims.

# Reframed abstract and introduction (draft)

Framing change: the contribution is a **maintenance policy for AI assets under foundation-model upgrades**
(retrain vs. transfer vs. wait). The option-pricing machinery is a tool for deriving the policy thresholds,
not the headline. Bracketed items [ ] are placeholders to fill from the final experiments.

Working title (alternatives):
- When to Retrain? The Economics of Maintaining Fine-Tuned Adapters Across Foundation-Model Upgrades
- Maintaining AI Assets Through Model Upgrades: Transfer, Retrain, or Wait

---

## Abstract

Organizations increasingly build business value on adapters (e.g., LoRA modules) fine-tuned on top of
foundation models they do not control. When the provider ships a new model version, every adapter is silently
invalidated, and the organization faces a recurring maintenance decision: retrain at full cost, transfer
the existing adapter to the new model, or keep operating a degraded asset. Existing IT-maintenance
and migration research does not address this setting, because the cost of transfer is now a design variable
rather than a fixed price: a transfer method can recover part of the lost performance cheaply, but how much it
recovers depends on how far the upgraded model drifted from its predecessor.

We develop a model of this decision in which upgrades arrive stochastically, adapter value evolves
randomly, and a transfer method is characterized by its performance recovery R and cost. We derive a threshold
policy: retrain once the value at stake exceeds a threshold that rises with recovery and with the upgrade
frequency (when upgrades are frequent, a repair is less likely to pay back). We characterize when a cheap but imperfect transfer method is worth using
(a bounded interval of adapter value, in multiples of retraining cost) and the maximum a firm should
pay for a method with a given recovery. To make recovery measurable, we propose Anchored Calibration Transfer (ACT),
a closed-form correction that uses unlabeled task inputs. In a controlled simulation, ACT raises recovery
from 0.49 (naive copy) to 0.69 under large drift, and the model implies that ACT is the cost-minimizing
policy for adapter values between roughly 0.5 and 6.7 times the retraining cost. [Real model pairs: ACT recovers
X% of retraining benefit at Y% of its cost on Z open-model pairs.]

Because the policy rests on assumptions about how upgrades arrive, we test robustness by simulating non-Poisson,
clustered and regular release schedules and jump risk in adapter value. Optimal thresholds shift by up to
[20-25]% (earlier retraining when releases cluster, later when they are regular), but the cost penalty of using the
baseline thresholds stays below [2.5]% and the transfer-optimal region persists. The results give managers a
concrete rule for AI-asset maintenance and give model providers evidence on the value of upgrade-compatible
design.

**Keywords:** AI asset management, foundation model upgrades, parameter-efficient fine-tuning, maintenance
policy, IT investment, transfer learning

---

## 1. Introduction

**The problem.** Firms now deploy generative AI largely by adapting foundation models they license rather than
build. A bank fine-tunes an adapter for contract review; a hospital for coding clinical notes. These adapters
are valuable assets, but they are tied to a specific version of a model controlled by someone else. Providers
release new versions several times a year, and an adapter trained against the old version no longer fits the new
one. Unlike traditional software upgrades, the break is not a visible interface change but a silent
loss of performance, and the remedy (retraining, with fresh data, compute, and revalidation) is costly.

**The decision.** After each upgrade the firm chooses among (i) retraining the adapter on the new model,
(ii) reusing the old adapter as is, possibly degraded, and (iii) transferring it with a cheaper correction method.
The timing matters as much as the choice: a degraded adapter that serves a low-stakes task can be left alone,
while a high-stakes one justifies immediate retraining, and the next upgrade may arrive before a retraining
investment pays back. This is a stochastic sequential decision, and no existing account tells managers where the
thresholds lie.

**Gap.** IS research on IT maintenance, migration, and technical debt treats upgrade costs as exogenous, and
the machine-learning literature on adapter transfer reports accuracy without asking when a given accuracy loss
justifies paying to fix it. What is missing is a link between a technical property of the transfer method
(its recovery R, the share of retraining benefit it restores) and a managerial outcome (the retrain-or-wait policy and
the willingness to pay for better transfer).

**What we do.** (1) We model the decision with stochastic upgrade arrivals and random adapter value, and derive a
closed-form threshold policy. (2) We show that transfer methods are valuable only within a bounded range of adapter
value and derive the maximum worthwhile cost of a method with recovery R. (3) We introduce ACT, a
closed-form, label-free correction that makes recovery high enough to matter, and measure recovery and cost on
[N] open-model pairs. (4) We test the policy's robustness to the upgrade-arrival assumption.

**Findings and contributions.**
- *Theory.* Optimal retraining thresholds rise with upgrade frequency and with recovery; the benefit of a
  transfer method is hump-shaped in adapter value.
- *Method.* ACT lifts recovery under large drift (0.49 to 0.69 in simulation) at a small fraction of retraining
  cost [C_A/C_N = ... measured].
- *Practice.* A manager can compute the retrain threshold from four observable quantities: upgrade frequency,
  value volatility, retraining cost, and measured recovery.
- *Robustness.* The transfer-optimal region and policy ranking survive clustered or regular release schedules and
  jump risk; only the timing threshold moves.

**Roadmap.** Section 2 reviews related work on IT maintenance and migration, AI asset management, and adapter
transfer. Section 3 sets up the model; Section 4 derives the policy; Section 5 introduces ACT; Sections 6 and 7
give numerical analysis and the model-pair experiments; Section 8 tests robustness; Section 9 discusses
implications and limits.

---

## Notes on what to tone down or keep

- Say "threshold policy derived by optimal stopping" instead of "real options" in title, abstract, and
  keywords; name the method once in Section 4 and cite the IT-investment real-options literature there.
- Keep the C_N caveat (compute only vs. data and revalidation labor) visible in the limitations; reviewers will ask.
- Fill every bracketed number from `results/pairs_summary.json` and `results/poisson_extensions.json`
  before submission; the 0.49 / 0.69 / 0.5-6.7 figures come from the toy simulation (`results/act_toy.json`,
  `results/real_options.json`).
- The first-person claims about firms (bank, hospital) are illustrations, not data; label them as such.
