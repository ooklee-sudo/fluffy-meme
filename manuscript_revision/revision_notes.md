# Revision notes for ISRE-2026-4468

Files:
- `revised_section4.md`: replacement text for Section 4.
- `verify_model.py`: brute-force check of every closed form and every number the paper reports. Run with `python3 verify_model.py`; it needs numpy only.

I only had the proof PDF (35 pages of main text), not the source files or the Online Appendix. The proofs given in the revised Section 4 are my own derivations, not the appendix's.

## What the editor's three complaints required

| Complaint | Fix in `revised_section4.md` |
|---|---|
| No utility function or decision problem | 4.2 states the decision utility, beliefs and sophistication (naive). 4.3 derives (1)–(3) from it by backward induction, and defines debt, self-admitted share, possession effect and lapse rate formally. |
| No players | 4.7.1 lists them: vendors, an organization and a developer. It also states each one's actions and payoffs. |
| "Equilibrium" not derived | 4.7.1 states timing, information, tie-breaking and the solution concept (subgame-perfect equilibrium). 4.7.2 proves Results 5–7 in the main text, including existence and uniqueness of the outcome under Bertrand competition. |

## What I verified

- Results 3, 5, 6 and 7 reproduce exactly (Result 6 in the Bertrand case).
- The Figure 2 bistable region reproduces: (0.646, 0.843).
- The Figure 3 text values reproduce: f_D = 0.05, f_O = 0.49, implementable 0.31.
- The Section 4.2–4.3 numbers reproduce, but only once the unreported parameters are filled in: s = 0.79, η = 0.5, λ = 1.
- The lapse rate of 0.21 is the *joint* probability q·P(plan, not do). The conditional rate is 0.27 per detected instance. The paper never says which it reports.

So the model is internally consistent and the paper's numbers are right. The problem was specification and presentation, not correctness.

## Issues in the original that the revision resolves

1. The results are stated without a utility function or a game.
2. The Result 3 statement says D "is decreasing in q" when α < ½. It is non-monotone, decreasing only on (q*, q̂).
3. The figure captions and Section 4.2–4.3 omit parameters (δ and v for Figure 3, λ for Figure 2, s, η).
4. The lapse rate is defined in words, but the number reported uses a different definition.

## Judgment calls you should make (they affect the claims)

1. **Noticing neglect (4.2).** Equation (3) values inspection at φq(1 − ηφ). A Bayesian posterior would divide by 1 − ηφ·φq. I kept the original formula and named the assumption. A referee may ask for the Bayesian version. Signs survive, but the closed forms change.
2. **Simultaneous vs sequential vendor game (4.7).** Result 6(a) for J ≥ 2 needs vendors to offer (f, p) simultaneously or entry to be contestable. With "friction first, price second", Shaked–Sutton vertical differentiation can sustain f ≠ f_D. Decide whether to defend simultaneous offers, or weaken "market structure affects the price, not the design".
3. **Section 4.5 treats the inspected share p as exogenous**, so φ, η and K play no role there. That is a simplification relative to 4.2 and should be said explicitly (I did say it).
4. **Constant rework cost in the game.** The closed forms in 4.7 assume a constant R̄ and uniform inspection time. The paper claims the sign results hold more generally (Appendix B). I could not check that.
5. **Results 4 and 8.** I restated them and checked Result 4 numerically, but I did not independently prove them.

## What this revision does not fix

- The paper is still theory only. The three empirical studies in Section 5 are proposals, not results. A reviewer at ISR may still want evidence.
- The contribution claim ("the distinctive change is the frame shift") rests on the behavioral wedges being plausible for developers. The model shows what follows if they hold. It does not show that they do.
- I have not edited Sections 1–3, 5–7 or the abstract. They may need small changes so the wording matches the new definitions (e.g. "lapse rate", "equilibrium").
