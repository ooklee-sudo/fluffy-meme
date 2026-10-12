# When to Retrain an LLM? A Dynamic Discrete Choice Model of AI Maintenance

Working research memo and paper skeleton (English). Numbers in Section 4 come from `rust_retrain.py`
(`results.json`); run `python rust_retrain.py --reps 100`.

## 1. Assessment of the research plan

**What is sound.** The setup is a direct Rust (1987) analogue: drift state x (mileage), retrain = engine
replacement, logit choice from EV1 shocks, NFXP. I re-implemented it from scratch and reproduced the plan's
numbers: threshold x* = 14, error rate 12.0 (2.4x baseline), counterfactual thresholds 10 / 14 / 21 for
RC = 20 / 40 / 80. The structural parameters are recovered (gamma ~ 0.50, RC ~ 40) from 3,000 periods.

**Problems to fix before the paper (ranked by how likely a referee is to raise them).**

1. **The state is unobserved in real data.** Rust observes mileage. "Accumulated drift" is not logged anywhere.
   You must build a measurable proxy (e.g., weeks since last release, embedding/distribution distance of
   user prompts to the training window, share of prompts mentioning post-cutoff entities). Everything
   downstream depends on this; the simulation sidesteps it. Treat the proxy as the central measurement section.
2. **Scale of utility is not identified.** Only RC/c is identified (c = loss per error) and the EV1 scale is
   normalized to 1. My runs fix c = 1, so "RC = 40" means "40 errors' worth of loss". To report dollars you
   need an external c (support-ticket cost, churn estimate). Say this explicitly.
3. **lambda0 drops out of the choice problem** (it appears in both utilities). It is identified only from the
   error process, not from retraining decisions. Fine, but state it.
4. **Retraining is not a single decision-maker's choice in open-source data.** Llama/Mistral/Qwen releases are
   driven by research roadmaps, benchmarks and competition, not a cost-minimizing operator. A structural
   "retraining cost" estimated here is a reduced-form shadow cost of a *release*. The enterprise (chatbot
   operator) data is therefore the identification-credible sample; open-source data is supporting evidence.
5. **Errors are not Poisson-clean.** Issue counts are overdispersed and depend on user base size and attention
   (a viral release spikes issues). Add exposure (users/downloads) as an offset; test overdispersion; use
   negative binomial. The plan already lists this; promote it to the baseline.
6. **Retraining is not a full reset.** A new release also changes behavior (new bugs, regression). Model a
   post-retrain state x0 > 0 or a "fresh-release bug" spike. Otherwise estimated RC absorbs this.
7. **Linear error rate lambda0 + gamma*x** can go negative in estimation; use a bounded form
   (e.g., exp link) or constrain. I use a floor.
8. **Two-step standard errors.** Plugging in estimated gamma then maximizing the choice likelihood understates
   uncertainty in RC. In my Monte Carlo the plug-in sd of RC is ~0.3 vs ~2.7 when gamma and RC are estimated
   jointly from choice data. Use the joint likelihood (error + choice) or a bootstrap / Murphy-Topel correction.
9. **Discount factor 0.95 weekly** implies a ~20-week horizon, short for model lifecycles. beta is not
   identified in this class of models; report sensitivity (my runs: x* = 16 / 14 / 13 for beta = 0.90 / 0.95 / 0.99).
10. **Competitor releases as state.** Making rival releases a shock to gamma or to the value of freshness
    (rather than a control variable) is the more interesting IS story and changes the Bellman equation.

## 2. Positioning for the paper

Theoretical angle: **AI depreciation as a maintenance-timing problem.** Contribution claims:

- Frame model drift as capital depreciation of an information-system asset; retraining as replacement.
- Show the retraining cost is structurally recoverable from the *timing* of updates (a "revealed cost").
- Counterfactuals: MLOps automation (lower RC) shortens cycles; faster drift (higher mu, e.g., fast-moving
  domains or competitor pressure) lengthens the tolerated error level and the retrain frequency in a
  quantifiable way.

Related literature to anchor (verify exact citations before submission):
Rust (1987, Econometrica); Hotz & Miller (1993) CCP estimation; Arcidiacono & Miller (2011);
Aguirregabiria & Mira (2010, survey); Duncan (1956) and the economic design of control charts;
Barlow & Hunter / Pierskalla & Voelker (1976) on maintenance optimization; concept drift (Gama et al., 2014,
ACM Computing Surveys); hidden technical debt in ML systems (Sculley et al., 2015); temporal degradation of
language models (Lazaridou et al., 2021, "Mind the gap"; Luu et al., 2022, "Time waits for no one").

## 3. Model (as specified, with fixes)

State x_t in {0,...,N}. Keep: x_{t+1} = min(x_t + D_t, N), D_t ~ Poisson(mu). Retrain: x_{t+1} = D_t.
Errors n_t ~ Poisson(lambda0 + gamma * x~_t) (x~ = post-decision state). Flow utility
u(x,0) = -c(lambda0 + gamma x) + e_0, u(x,1) = -RC - c*lambda0 + e_1, e ~ EV1(scale 1), c normalized to 1.
Bellman: V(x) = ln( exp{u0 + beta E[V(x')|x]} + exp{u1 + beta E[V(x')|0]} ).
Estimation: (i) mu from drift increments, (ii) (lambda0, gamma) by Poisson ML, (iii) RC by NFXP.
Recommended: joint likelihood over (error, choice) data.

## 4. Replication results

Fill from `results.json` (single run, Monte Carlo, sample-size sweep, counterfactuals).

## 5. Data and identification plan (revised priority)

1. Enterprise chatbot logs (weekly error reports + update history): primary, credible decision-maker.
2. Open-source releases (GitHub issues, HF discussions): descriptive validation, with exposure offset.
3. LMSYS-Chat-1M / WildChat: construct *drift proxies* and error proxies (re-asks, negative feedback), not retrain timing.

Minimum viable data: roughly 250+ weekly observations per firm-model pair to get RC within ~15% (see sample-size sweep);
otherwise pool across models with heterogeneity in RC.

## 6. Target journal route

Keep the plan's two-track idea: operations/OR version (EJOR, M&SOM) built on the model and counterfactuals;
IS version (MISQ/ISR) only if real enterprise data exist. Without real data, a MISQ submission is not viable.
