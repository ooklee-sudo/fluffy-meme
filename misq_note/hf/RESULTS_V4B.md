# Results: Amendment 1 analyses (plan: ANALYSIS_PLAN_V2RELABEL.md, Amendment 1; code: analysis_v4b.py; numbers: results_v4b.json; figure: figs/fig_forest_labelsets.png)

**F1 Matched placebo.** Placebo times restricted to the 20% of candidates whose directional 30-minute return before the placebo time is nearest to the event's own (mean directional pre-30 of events: +0.57 de-escalation, +0.22 escalation). De-escalation: observed +1.04%; placebo mean +0.10, 95th percentile 0.27, 99th 0.33; share of 10,000 draws ≥ observed 0. Escalation: observed +0.48%; placebo mean +0.09, 95th percentile 0.26, 99th 0.32; share 0. The post-window move exceeds comparable-drift placebos.

**F2 Next-open returns for signal posts without a window** (human labels, three-hour filter; directional log return from the last tick before the post to the first tick after the reopening; median gap about 49 hours, so it contains all weekend news). Escalation: n = 15, mean +4.14%, median +3.94%, 14 of 15 positive. De-escalation: n = 8, mean −0.10%, median −1.47%, 3 of 8 positive. Descriptive only; the gap return is not attributable to the post.

**F3 Discordant-event decomposition** (95 events; mean directional return in the direction of the model's class).
| Model labels | Model class | Model-labelled events | Also human class | Human de-escalation | Human mixed | Human other | Human escalation |
|---|---|---|---|---|---|---|---|
| Model 1 | Escalation | 24 | 10 (+0.45) | 4 (−0.43) | 5 (+0.71) | 5 (−0.44) | — |
| Model 1 | De-escalation | 34 | 23 (+1.15) | — | 4 (+0.99) | 6 (+0.23) | 1 (−1.30) |
| v2 majority | Escalation | 30 | 14 (+0.53) | 2 (−0.84) | 8 (+0.71) | 6 (−0.30) | — |
| v2 majority | De-escalation | 33 | 24 (+1.06) | — | 4 (+0.99) | 5 (+0.38) | 0 |
The attenuation of the escalation estimate under model labels comes from events the model adds: posts that humans call de-escalation or other have mean directional returns of −0.3 to −0.8 in the escalation direction, while posts that humans call mixed have +0.71. This is event selection into the class, not noise shrinking the same effect.

**F4 Two-sided p for the robustness variants** (post ≠ 0; post − pre). Baseline: de-escalation post ≠ 0 p < .001, post − pre p = .059; escalation p = .013, .117. Cluster rules 0/1/2/6 h: post − pre p = .053/.077/.059/.127 (de-escalation), .142/.142/.089/.194 (escalation). Consensus only: .090 and .156 (escalation n = 7). Window 5 min: de-escalation .006, escalation .193; 15 min: .011 and .039; 60 min: .731 and .173. Dropping the three big-day events: .049 and .117. At 30 minutes the post − pre excess is not significant at 5% two-sided in most variants.

**F5 Forest plot** of class means and day-clustered 95% CI by label set (figs/fig_forest_labelsets.png).
