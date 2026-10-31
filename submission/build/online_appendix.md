# Online Appendix

**Fewer Clicks, Not Fewer Searches: Generative AI and the Monetization of Search**

## Appendix A. Proofs
Let k ≡ γ/(2t), so x̂ = 1/2 + k(a\_E − a\_I). The AI profits are π\_I = s·x̂·(m\_I a\_I − c) and π\_E = s·(1 − x̂)·(m\_E a\_E − c).

**Proof of Proposition 1.** For the incumbent,

$$
\frac{\partial \pi_I}{\partial a_I} = s\left[m_I \hat{x} - k\,(m_I a_I - c)\right], \qquad \frac{\partial^2 \pi_I}{\partial a_I^2} = -2 s k m_I < 0
$$

At a\_I = 0, profit is −s·x̂·c < 0 and the derivative is s(m\_I x̂ + kc) > 0. A small increase in a\_I therefore strictly raises profit, so a\_I = 0 is not a best response. The argument for E is symmetric. ∎

**Proof of Proposition 2.** Strict concavity implies that best responses are given by the first-order conditions:

$$
a_I = \frac{1}{4k} + \frac{a_E}{2} + \frac{c}{2m_I}, \qquad a_E = \frac{1}{4k} + \frac{a_I}{2} + \frac{c}{2m_E}
$$

Each best response has slope 1/2, so the best-response map is a contraction and the equilibrium is unique. Substituting the second condition into the first gives (3/4)a\_I = 3/(8k) + c/(2m\_I) + c/(4m\_E). Using 1/(2k) = t/γ yields the stated a\_I^e; a\_E^e follows by symmetry. Then a\_E^e − a\_I^e = (c/3)(1/m\_E − 1/m\_I), which gives x̂^e.

From the incumbent's first-order condition, m\_I a\_I − c = m\_I x̂/k = 2t·m\_I·x̂/γ. Hence π\_I = s·x̂·(2t·m\_I·x̂/γ) = s·(2t·m\_I/γ)·x̂².

(a) With m\_I = m\_E = m, a^e = t/γ + c/m; the comparative statics are immediate. (b) The margin is m·a^e − c = m·t/γ and x̂^e = 1/2, so profit is s·m·t/(2γ), independent of c; and ∂(m·a^e)/∂c = 1. (c) If m\_I > m\_E, then a\_I^e − a\_E^e = (c/3)(1/m\_I − 1/m\_E) < 0 and x̂^e > 1/2. Interiority requires (γc/(6t))·|1/m\_E − 1/m\_I| < 1/2. ∎

**Proof of Proposition 3.** With a\_E = 0 and m\_I = m, the incumbent's best response is a\_I = 1/(4k) + c/(2m) = t/(2γ) + c/(2m). Then x̂ = 1/2 − k·a\_I = 1/4 − γc/(4tm), which is positive if and only if m·t > γ·c. The margin is m·a\_I − c = (m·t − γ·c)/(2γ), and x̂ = (m·t − γ·c)/(4tm). Multiplying gives π\_I = s(m t − γ c)²/(8γ m t). Dividing by the symmetric-equilibrium profit s·m·t/(2γ) gives (1/4)(1 − γc/(mt))² ≤ 1/4. The entrant's profit is −s(1 − x̂)c < 0. ∎

**Proof of Proposition 4.** Equilibrium ad intensities do not depend on s, because s multiplies both AI profit functions. Write π\_I^AI = s·φ, where φ is the incumbent's equilibrium AI profit per AI-amenable query. Then Π\_I = (1 − s)R + sφ and dΠ\_I/ds = φ − R. (i) With a\_I = 0, φ = −x̂c < 0, so dΠ\_I/ds < −R < 0 and Π\_I → −x̂c < 0 as s → 1. (ii) In the symmetric equilibrium φ = m·t/(2γ), so dΠ\_I/ds ≥ 0 if and only if m ≥ 2γR/t. ∎

**Proof of Proposition 5.** Each platform takes m as given, so the first-order conditions of Proposition 2 apply with m\_I = m\_E = m. In the symmetric equilibrium, a = t/γ + c/m and x̂ = 1/2, so A = (1 − s)ā + s(t/γ + c/m). Substituting into m = μ − ηA and multiplying by m gives m² − Bm + ηsc = 0. Real roots exist if B² ≥ 4ηsc. The larger root is the stable one: there, 2m − B = √(B² − 4ηsc) > 0, which is equivalent to 1 − ηsc/m² > 0. Differentiating the quadratic in c gives (2m − B)·dm/dc = −ηs, hence dm/dc = −ηs/√(B² − 4ηsc) < 0. Incumbent AI profit s·m·t/(2γ) and legacy revenue (1 − s)mā are increasing in m and therefore decrease in c. ∎

**Proof of Proposition 6.** Holding a\_I fixed, differentiate Π\_I with respect to a\_E. Through x̂, the AI term changes by s·k·(m a\_I − c). Through m, the legacy and AI terms change by \[(1 − s)ā + s x̂ a\_I\]·∂m/∂a\_E = V\_I·∂m/∂a\_E, where ∂m/∂a\_E = −η·∂A/∂a\_E = −ηs\[(1 − x̂) + k(a\_I − a\_E)\]. The incumbent's first-order condition (with m given) is k(m a\_I − c) = m x̂. Substituting yields the stated expression. At the symmetric equilibrium, x̂ = 1/2 and a\_I = a\_E, so ∂Π\_I/∂a\_E = (s/2)(m − ηV\_I). This is positive if and only if ηV\_I/m < 1. Writing ηV\_I/m = (ηA/m)(V\_I/A) = εw\_I gives the condition. ∎

**Proof of Proposition 7.** In the symmetric equilibrium, the incumbent's AI margin is m·a − c = m·t/γ and its share is 1/2, so Π\_I = (1 − s)mā + s·m·t/(2γ) = mΛ. Then dΠ\_I/ds = m·Λ'(s) + Λ·m'(s), with Λ'(s) = t/(2γ) − ā. Differentiating m = μ − η\[(1 − s)ā + s(t/γ + c/m)\] with respect to s gives m' = η(ā − a) + ηsc·m'/m², so m' = η(ā − a)/(1 − ηsc/m²). The denominator is positive at the stable root (Proposition 5), so m' has the sign of ā − a. With η = 0, the condition dΠ\_I/ds ≥ 0 reduces to t/(2γ) ≥ ā, that is, m·t/(2γ) ≥ mā = R, as in Proposition 4. ∎

**Proof of the Lemma in Section 4.6.** With the incumbent's format fixed, x̂ = 1/2 + (γa\_E − g)/(2t), and the entrant maximizes s(1 − x̂)(m a\_E − c), which is strictly concave in a\_E. The first-order condition is m(1 − x̂) = k(m a\_E − c) with k = γ/(2t). Substituting 1 − x̂ = 1/2 − k a\_E + g/(2t) gives a\_E = (t + g)/(2γ) + c/(2m). Then γa\_E = (t + g)/2 + γc/(2m), and x̂ = 1/2 + \[(t + g)/2 + γc/(2m) − g\]/(2t) = (3t − g)/(4t) + γc/(4tm). The incumbent earns r on each of its x̂ queries. ∎

**Proof of Proposition 8.** (i) Summaries dominate links if (R − c\_O)x̂(Δ − Δ\_O) > R·x̂(Δ). Multiplying by 4t and rearranging gives RΔ\_O > c\_O(3t − Δ + Δ\_O + γc/m). (ii) Full answers dominate summaries if m·t/(2γ) ≥ (R − c\_O)·\[(3t − Δ\_H)/(4t) + γc/(4tm)\]. Multiplying by 4t/(R − c\_O) gives 2mt²/(γ(R − c\_O)) ≥ 3t − Δ\_H + γc/m, which rearranges to Δ\_H ≥ Δ\_H\*. (iii) ∂Δ\_H\*/∂R = 2mt²/(γ(R − c\_O)²) > 0; ∂Δ\_H\*/∂c = γ/m > 0; ∂Δ\_H\*/∂m = −γc/m² − 2t²/(γ(R − c\_O)) < 0; ∂Δ\_H\*/∂c\_O = −2mt²/(γ(R − c\_O)²) < 0. The corollary follows because Δ\_H\* is finite while m·t/(2γ) < R is a separate restriction on parameters; both can hold at once (for example, t = γ = 1, m = 2, c = 0.3, R = 1.4, c\_O = 0.05 gives Δ\_H\* ≈ 0.19 and m·t/(2γ) = 1 < R). ∎

**Proof of Proposition 9.** Fix a date d and let h(σ, d) = σ\[π\_A − (R\_0 − c\_O)x̂\_H(d)\] − R\_1x̂\_H(d)σ². Since R\_1x̂\_H(d) > 0, h is strictly concave in σ, so the set S(d) = {σ : h(σ, d) ≥ K} is an interval, possibly empty. Moreover ∂h/∂d = −x̂\_H'(d)\[(R\_0 − c\_O)σ + R\_1σ²\] > 0 for σ > 0, because x̂\_H' < 0 and R\_0 > c\_O; hence S(d) ⊆ S(d') for d < d'. The lower contour sets of the switching date, {σ : D(σ, K) ≤ d} = S(d), are therefore nested intervals, which is the definition of quasi-convexity of D in σ and gives part (i). For part (ii), a higher K shrinks S(d) at every d, so D weakly rises. Part (iii) follows because an engine outside every S(d) never satisfies the switching condition, and a fall in K enlarges every S(d). ∎

**Proof of Proposition 10.** G is continuous and decreasing in θ, and T is continuous and decreasing in ω, so Φ = T ∘ G is continuous and increasing. Since ω ∈ \[0, 1\], Φ maps \[q, θ̄\] into itself, where θ̄ = 1 − (1 − q)ζ, and by Brouwer's theorem (or Tarski's, since Φ is increasing) a fixed point exists. (i) At a fixed point, θ = 1 − (1 − q)\[ζ + (1 − ζ)ω\], so θ − q = (1 − q)(1 − ζ)(1 − ω) ≥ 0, decreasing in ω. (ii) At the lower end of the interval Φ(q) ≥ q, and at the upper end Φ(θ̄) ≤ θ̄. If Φ crosses the 45-degree line from below at an interior fixed point θ₂, continuity implies at least one fixed point in \[q, θ₂) where Φ crosses from above and one in (θ₂, θ̄\]. Under the adjustment θ\_{n+1} = Φ(θ\_n), fixed points where Φ crosses from above are stable and θ₂ is unstable; the lowest has the most clicks (vigilant) and the highest the fewest (complacent). (iii) If e/(1 − q) exceeds the upper bound of the support of F, then G(θ) = 0 for all θ ≥ q, so Φ is constant at θ̄, its unique fixed point. (iv) Φ is decreasing in ζ at every θ. For ζ large enough, Φ lies below the 45-degree line on (θ₂, θ̄\], so the monotone sequence θ\_n falls below θ₂ in finite time. When ζ returns to its original value, θ\_n lies in the basin of the vigilant equilibrium and converges to it. ∎

## Appendix B. Data and Replication Package

All analyses use publicly available data. The replication package (replication_package.zip) contains the data-collection scripts, the analysis scripts that produce each table and figure, the numerical examples for Propositions 8–10, small hand-coded datasets (event dates, rollout dates by edition and country, launch dates and revenue for 17 search engines), and the processed data for the trust-shock analysis. Its README maps every script to the corresponding table or figure and lists data sources, access dates, run order, and software requirements.

Raw data that third parties do not permit us to redistribute (for example, Google Trends extracts and Wikimedia hourly dump files) are re-downloaded by the collection scripts. Google Trends is rate-limited and returns sampled indices, so re-downloaded series can differ slightly from ours.

**Data sources.** Wikimedia hourly projectviews dumps (dumps.wikimedia.org); Google Trends (via pytrends); Eurostat datasets isoc_ai_iaiu and isoc_ci_ifp_fu; World Bank World Development Indicators (NY.GDP.PCAP.CD, IT.NET.USER.ZS, SP.POP.TOTL); StatCounter Global Stats; Alphabet, Meta, and Microsoft filings on SEC EDGAR (Forms 8-K, 10-Q, XBRL); daily stock prices for the event study; and launch dates from company announcements, archived help pages, and trade press as cited in the text. All sources were accessed in October 2026.

**Figure data.** The values plotted in Figures 1–5 are provided in figures/figure_data/ together with the plotting script (make_figures.py).
