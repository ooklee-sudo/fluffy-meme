# Fewer Clicks, Not Fewer Searches: Generative AI and the Monetization of Search

Oct 30, 2026 · @ook

**Abstract.** Generative AI is widely expected to displace web search. We argue that the more immediate threat to search platforms is subtler: AI-generated answers resolve queries without the click on which sponsored search is priced. Using Google Trends data for U.S. states and Wikipedia pageviews matched to Eurostat's official statistics on generative AI use, we find little evidence that AI adoption has reduced aggregate search activity, even though individual chatbot adopters search less. Exploiting the staggered international rollout of Google's AI Overviews, we find suggestive evidence that AI summaries reduce clicks to external sites. We then develop a model in which an incumbent search platform competes with an AI-native entrant whose answers are costly to produce. The model's most robust implication is that ad-free answers are not sustainable; it also shows how inference costs are shared between users and advertisers and why a rival's adoption of advertising need not benefit the incumbent. A cannibalization channel in the model predicts that firms with larger legacy search businesses should delay full AI answers. We find no support for this prediction: across 17 search engines, and across 47 countries within Google, the timing of deployment reflects technical capability, market scale, and regulation rather than legacy revenue. A widely publicized trust shock in May 2024 was not followed by more clicks, which suggests that convenience rather than trust draws users away from search results. These findings recast the economics of AI search as a problem of monetizing answers rather than retaining searches.

**Keywords:** generative AI, search engines, click-through, sponsored search, AI Overviews, advertising, natural experiment, two-sided platforms, inference cost

## 1. Introduction

On October 29, 2026, Alphabet's shares fell by roughly 13%, their largest single-day decline since the company's 2004 listing, erasing about $475 billion in market value (Yahoo Finance 2026). The proximate cause was a quarterly report showing that revenue from Google Search had grown by 12%, a marked deceleration from 19% and 17% in the two preceding quarters, even though query volume had grown at its fastest pace in five years (Alphabet 2026a). Management attributed part of the slowdown to the “lower monetization” of AI Mode, Google's conversational answer interface. Users, in other words, were searching more, but their searches were earning less.

It is often argued that generative AI will make search engines obsolete. The episode above points to a different and, we suggest, more immediate threat. For two decades, search engines have monetized *intent*: a user reveals a need through a query, and the platform sells the adjacent attention to advertisers, who pay when the user clicks. Generative AI changes the unit of output from a ranked list of links to a synthesized answer. When that answer satisfies the user, the click on which sponsored search depends may never occur, even though the search itself does. Each answer, moreover, consumes inference compute that a list of links does not. The danger for search platforms therefore lies less in fewer searches than in fewer clicks, and hence less revenue, per search.

This paper examines that transition both empirically and theoretically. We address four questions:

1. Does the adoption of AI reduce the use of search, or mainly the clicks that follow a search?
2. Can AI answers remain ad-free in equilibrium, and who ultimately bears their inference cost?
3. Do incumbents with larger legacy search businesses delay full AI answers, as theories of cannibalization would predict?
4. Do users stop clicking because they trust AI answers, or because reading search results is costly?

We begin with the premise. Across 51 U.S. states and 24 European Wikipedia editions matched to Eurostat statistics, places with higher AI adoption did not experience larger declines in search-related activity. The staggered rollout of Google's AI Overviews, by contrast, offers suggestive evidence that AI answers reduce clicks out of search: desktop Wikipedia views fell by roughly 9% after launch, although the estimate lies at the margin of statistical significance. Together with browsing evidence that users click a result about half as often when an AI summary is present (Chapekis 2025) and panel evidence that individual chatbot adopters run about 20% fewer traditional searches (Padilla et al. 2026), these results suggest that what has changed most is the number of clicks per search. That is the margin on which our model operates.

We then develop a model in which an incumbent with a legacy search business competes with an AI-native entrant for queries that users would rather have answered directly. Consumers dislike advertising, platforms choose how much advertising to place in their answers, and each answer carries an inference cost. Extensions make the price of advertising endogenous, let the incumbent choose between summaries and full answers, introduce a fixed cost of answer technology, and model how users come to trust AI answers. Several results hold under weak conditions. Ad-free answers are never a best response (Proposition 1). Inference costs are passed on to users as additional advertising, fully when the ad price is fixed and partially when advertiser demand slopes downward (Propositions 2 and 5). A rival's advertising helps the incumbent by making the rival less attractive but hurts it by depressing the ad price (Propositions 3 and 6). And with a fixed cost of answer technology, firms with scale and in-house models deploy full answers first (Proposition 9). Other results rest on cannibalization. Advertising in AI answers restores the incumbent's profit only above a threshold of ad productivity, which ad-light answers lower (Propositions 4 and 7), and an incumbent with more legacy profit keeps summaries longer before switching to full answers (Proposition 8). Finally, because users learn about errors mainly when they verify, they tend to overtrust AI answers and can settle into either a complacent or a vigilant equilibrium (Proposition 10).

The evidence supports the first set of results but not the cannibalization channel. Alphabet's market value fell on news that AI was displacing search while Meta's did not (pooled Z = −4.32), and Google's announcement of ads in AI Mode was followed by an abnormal return of 6.0%. A rival's adoption of advertising had no measurable effect, which Proposition 6 can accommodate when advertiser demand is close to unit-elastic, and since 2023 Alphabet's cost-per-click growth has moved almost one-for-one against its paid-click growth, as a scarcity dividend would imply. Legacy profit, however, does not predict when full answers arrive. Across 17 search engines, those with larger legacy search revenue did not move later; Bing, which had the second-largest legacy revenue in our sample, moved first, helped by its access to OpenAI's models. Within Google, AI Mode arrived later where regulators intervened and earlier in larger markets, while markets in which queries are worth more to advertisers were not delayed. The widely publicized AI Overviews errors of May 2024, a shock to trust that left the effort of reading results unchanged, were not followed by a rise in clicks, which suggests that convenience rather than trust keeps users from reading search results.

The paper contributes to three streams of IS research. For research on sponsored search, we show that generative answers shift the relevant margin from the number of searches to the number of clicks per search, and we provide early quasi-experimental evidence of that shift. For research on competition between ad-supported and paid platforms (e.g., Casadesus-Masanell and Zhu 2010), we add a marginal production cost per interaction and an advertiser side, which together determine who bears the cost of AI. For research on IT-enabled disruption, we formalize the innovator's dilemma for search and test its central prediction with cross-firm and within-firm data. The prediction fails: incumbents with more to lose did not delay full AI answers, which points instead to capability, scale, and regulation as the constraints that govern how quickly incumbents respond to generative AI.

The remainder of the paper is organized as follows. Section 2 reviews related work. Section 3 presents the model and Section 4 its equilibrium analysis and extensions. Section 5 reports the empirical analysis, Section 6 discusses managerial and policy implications, and Section 7 concludes.

## 2. Related Literature

This paper draws on several literatures that have developed largely in isolation from one another: empirical work on generative AI and information search, the economics of sponsored search, the newer design literature on advertising inside model output, two-sided platforms, competition between ad-funded and paid business models, and research on IT-enabled disruption. The first of these has grown quickly since 2023, and Table 1 lists the empirical studies closest to ours.

*Generative AI and information search.* Early experiments found that chatbots complete many search tasks about as accurately as a search engine and in less time, although users check facts less carefully ([Xu, Feng, and Chen 2023](https://papers.ssrn.com/abstract=4498671)) and learn less deeply from what they read ([Melumad and Yun 2025](https://doi.org/10.1093/pnasnexus/pgaf316)). Whether chatbots actually replace search in the field depends a good deal on the level at which one looks. At the individual level the answer appears to be yes: in a Comscore panel, users who adopted a chatbot ran more than 20% fewer traditional searches after roughly five months, a decline concentrated in question-type queries, while navigational searches and exposure to search ads held steady ([Padilla, Lam, Lambrecht, and Hollenbeck 2026](https://www.msi.org/working-paper/the-impact-of-llm-adoption-on-online-user-behavior/)). Destination sites tell a similar story where AI can stand in for their content. Stack Overflow lost about a quarter of its activity ([del Rio-Chanona, Laurentsyeva, and Wachs 2024](https://kti.krtk.hu/en/publikacio/r-maria-del-rio-chanona-nadzeya-laurentsyeva-johannes-wachss-article-in-the-pnas-nexus-2024/); [Burtch, Lee, and Chen 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11074245/)), and Wikipedia articles that overlap with ChatGPT's knowledge lost views and edits ([Lyu et al. 2025](https://arxiv.org/abs/2503.00757)). In the aggregate, however, Wikipedia engagement did not fall during ChatGPT's first year ([Reeves, Yin, and Simperl 2024](https://arxiv.org/abs/2405.10205)).

The clearest effects come from AI summaries placed inside the search page itself. In a field experiment that hid Google's AI Overviews from participants, outbound organic clicks per search rose from 0.37 to 0.62, but sponsored clicks were unaffected ([Agarwal and Sen 2026](https://ppc.land/ai-overviews-cut-publisher-clicks-39-8-in-first-randomized-study/)). Using the staggered international rollout of the same feature, [Khosravi and Yoganarasimhan (2026)](https://arxiv.org/abs/2602.18455) estimate a reduction of about 5% in search referrals to English Wikipedia. AI Overviews now appear on roughly half of all queries and tend to cite different sources, Google-owned ones more often, than the organic results beneath them ([Grossman et al. 2026](https://arxiv.org/abs/2604.27790)). Finally, the traffic that chatbots do send onward behaves differently from search traffic once it reaches retail sites ([Kaiser and Schulze 2026](https://pubsonline.informs.org/doi/10.1287/mksc.2025.0489)).

Table 1. Empirical studies of generative AI and search, 2023–2026.

| Study | Data and design | Main finding | Relation to this paper |
| --- | --- | --- | --- |
| [Agarwal and Sen (2026)](https://ppc.land/ai-overviews-cut-publisher-clicks-39-8-in-first-randomized-study/) | Field experiment; browser extension hides AI Overviews; 1,065 U.S. desktop users | Organic clicks per search 0.37 with vs. 0.62 without AI Overviews; sponsored clicks unchanged | AI summaries cut clicks, but not ad clicks |
| [Khosravi and Yoganarasimhan (2026)](https://arxiv.org/abs/2602.18455) | Difference-in-differences; staggered AI Overviews rollout; English vs. German and French Wikipedia articles | About 5% fewer search referrals to English Wikipedia | Same design family as our Test C |
| [Padilla, Lam, Lambrecht, and Hollenbeck (2026)](https://www.msi.org/working-paper/the-impact-of-llm-adoption-on-online-user-behavior/) | Comscore desktop panel, 2022–2023; staggered adoption of chatbots | Adopters' traditional searches fall more than 20%; search-ad exposure unchanged; small sites lose most | Individual-level evidence of substitution |
| [Grossman et al. (2026)](https://arxiv.org/abs/2604.27790) | 11,500 real queries run on Google Search, AI Overviews, and Gemini | AI Overviews on 51.5% of queries; sources differ sharply from organic results | Describes the treatment |
| [Kaiser and Schulze (2026)](https://pubsonline.informs.org/doi/10.1287/mksc.2025.0489) | 973 e-commerce sites, Aug. 2024–July 2025 | Compares ChatGPT referrals with search and other channels | Value of AI-referred traffic |
| [Chapekis (2025), Pew](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/) | Browsing data of 900 U.S. adults, March 2025 | Click on a result in 8% of visits with an AI summary vs. 15% without | Clicks per search |
| [Lyu et al. (2025)](https://arxiv.org/abs/2503.00757) | Difference-in-differences across Wikipedia articles by similarity to ChatGPT | Declines concentrated in articles ChatGPT can substitute for | Substitution is query-specific |
| [Reeves, Yin, and Simperl (2024)](https://arxiv.org/abs/2405.10205) | 12 Wikipedia language editions | No aggregate decline in engagement in the first year | Aggregate null |
| [del Rio-Chanona et al. (2024)](https://kti.krtk.hu/en/publikacio/r-maria-del-rio-chanona-nadzeya-laurentsyeva-johannes-wachss-article-in-the-pnas-nexus-2024/); [Burtch, Lee, and Chen (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11074245/) | Stack Overflow vs. control platforms | Activity down about 25%, most where ChatGPT performs well | Substitution of AI for web Q&A |
| [Xu, Feng, and Chen (2023)](https://papers.ssrn.com/abstract=4498671); [Melumad and Yun (2025)](https://doi.org/10.1093/pnasnexus/pgaf316) | Controlled experiments | Similar accuracy, less time; shallower learning with LLM summaries | Quality of AI answers vs. links |

*Sponsored search.* Most of what we know about the economics of search advertising comes from the study of position auctions. Edelman et al. (2007) and Varian (2007) characterize equilibrium in the generalized second-price auction, and a large body of IS and marketing research shows how rank, relevance, and query intent shape click-through and conversion (Ghose and Yang 2009, Agarwal et al. 2011). All of this work takes the ranked results page for granted. An answer engine replaces that page with generated text, so the platform no longer chooses only which ads to rank; it chooses how much commercial content to weave into the answer. We set the auction aside and model that choice of ad intensity directly.

*Advertising inside generated content.* A fast-growing literature in computer science and economics asks how ads could be sold within LLM output. [Feizi et al. (2023)](http://www.sigecom.org/exchanges/volume_22/2/FEIZI.pdf) lay out the opportunities and the risks. [Duetting et al. (2024)](https://arxiv.org/pdf/2310.10826) propose token-level auctions in which advertisers' own language models steer the generated text; [Dubey et al. (2024)](https://arxiv.org/abs/2404.08126) auction the prominence of ads within a summary; [Hajiaghayi et al. (2024)](https://arxiv.org/abs/2406.09459) allocate ads across discourse segments in retrieval-augmented generation; and [Balseiro et al. (2025)](https://arxiv.org/abs/2506.03309) extend the position auction to sponsored content blended into answers. On the publisher side, [Aggarwal et al. (2024)](https://arxiv.org/abs/2311.09735v3) show that content creators can raise their visibility in generative answers by as much as 40% through what they call generative engine optimization. These studies are concerned with mechanism design and take as given that the platform will sell ads. Our question comes one step earlier: whether ads should appear in AI answers at all, in what quantity, and under which competitive conditions.

*Two-sided platforms.* Rochet and Tirole (2003), Parker and Van Alstyne (2005), and Armstrong (2006) show that platforms set prices to balance participation on each side, often subsidizing the side whose presence is worth more to the other. Anderson and Coate (2005) treat advertising as a nuisance that viewers pay for with attention rather than money. We adopt their view of ads as a nuisance and add one feature that sets generative AI apart from earlier media: serving each user interaction carries a meaningful marginal cost.

*Ad-funded versus paid competition.* Prasad et al. (2003) ask when a media firm should combine subscription fees with advertising, and Casadesus-Masanell and Zhu (2010) study how an incumbent should respond to an ad-sponsored entrant. Two recent papers bring these questions to generative engines. [Zhang, Jiao, Li, and Xiong (2026)](https://arxiv.org/abs/2603.29071) derive a dynamic cutoff rule under which an ad is shown only when its immediate payoff exceeds the long-run value of keeping the answer clean, and they show that competition moves the cutoff toward ad-free answers. [Wang et al. (2025)](https://link.springer.com/chapter/10.1007/978-3-031-94184-9_2) analyze the choice of revenue model between two AI platforms. Our setting is in a sense the mirror image of Casadesus-Masanell and Zhu (2010): the incumbent has a legacy search business, and it is the entrant that may stay ad-free. What distinguishes our model from these is the combination of a per-answer inference cost and an explicit advertiser side. Together they determine who ends up paying for AI answers, and they explain why a rival's decision to carry ads need not help the incumbent.

*IT-enabled disruption and cannibalization.* Christensen (1997) describes how incumbents underinvest in technologies that would cannibalize a profitable core business. Search offers an unusually clean version of this dilemma: the incumbent must offer AI answers to keep its users, yet every AI answer replaces a query that was already well monetized. We derive the condition under which advertising in AI answers resolves the dilemma, and we then test the prediction, implicit in Christensen's account, that firms with more to lose should move later. That prediction turns out not to hold.

*Position of this paper.* We see four differences from prior work. First, existing empirical studies measure either user behavior (searches and clicks) or outcomes at destination sites (Wikipedia, Stack Overflow, publishers). We follow these effects through to the search platform's own revenue, using stock-market reactions and Alphabet's reported paid clicks and cost per click. Second, the finding that AI Overviews reduce organic but not sponsored clicks (Agarwal and Sen 2026; Padilla et al. 2026) sharpens the question our model addresses. Revenue per search is at risk less from summaries that sit above the results than from answers that replace the results page altogether, as in AI Mode and stand-alone chatbots. Third, our rollout analysis extends Khosravi and Yoganarasimhan (2026) to 25 Wikipedia language editions and several launch cohorts, separates desktop from mobile traffic, and adds a test of whether trust or effort drives the loss of clicks. Fourth, on the theory side, no existing model of generative engines combines a legacy search business, inference cost, and an advertiser side. This combination produces our results on cost pass-through, on the effect of a rival's ads, and on the scarcity dividend, and it yields predictions about the timing of AI rollouts that we take to data on 17 search engines and on Google's launches in 47 countries.

## 3. Model

**Queries.** A unit mass of queries arrives each period. A fraction s ∈ \[0, 1\] is *AI-amenable*: users prefer a synthesized answer to a list of links. We treat s as exogenous and increasing over time as model quality improves. The remaining 1 − s queries stay in legacy search, where the incumbent is the only platform and earns profit R > 0 per query. Before AI answers existed, the incumbent served all queries and earned R per query.

**Platforms.** An incumbent I (a search platform that also offers AI answers) and an entrant E (an AI-native answer engine) compete for AI-amenable queries. Each platform j ∈ {I, E} chooses an ad intensity a\_j ≥ 0 for its AI answers. An answer with ad intensity a\_j earns advertising revenue m\_j a\_j, where m\_j > 0 is ad productivity: how much advertisers pay per unit of ad exposure. It reflects targeting precision, advertiser reach, and auction depth. Every answer costs c > 0 in inference compute, regardless of platform. Platform j's margin per AI answer is m\_j a\_j − c.

**Consumers.** Users of AI-amenable queries are uniformly distributed on \[0, 1\], with I located at 0 and E at 1. A user at x obtains

```latex
U_I(x) = v - \gamma a_I - t x, \qquad U_E(x) = v - \gamma a_E - t(1 - x)
```

where v is the gross value of an answer, γ > 0 is ad nuisance (the disutility per unit of ad intensity), and t > 0 captures horizontal differentiation, such as ecosystem integration, default placement, brand trust, or answer style. We assume v is large enough that the market is covered. The indifferent user is

```latex
\hat{x} = \frac{1}{2} + \frac{\gamma}{2t}(a_E - a_I)
```

**Payoffs.** The incumbent's profit and the entrant's profit are

```latex
\Pi_I = (1 - s)R + s\,\hat{x}\,(m_I a_I - c), \qquad \Pi_E = s\,(1 - \hat{x})(m_E a_E - c)
```

Platforms choose ad intensities simultaneously. We focus on interior pure-strategy Nash equilibria (0 < x̂ < 1). The term (1 − s)R is unaffected by a\_I, so the incumbent's ad choice maximizes its AI profit. The legacy business matters for the incumbent's overall trajectory as s rises, which we analyze in Proposition 4.

**Discussion of assumptions.** Ad intensity enters revenue linearly and consumer utility linearly, as in Anderson and Coate (2005). This captures the trade-off between answer quality and commercial content: more sponsored content raises revenue per answer but degrades the user's experience. The cost c is what distinguishes AI answers from earlier information goods, whose marginal cost is close to zero. Allowing m\_I ≠ m\_E captures the incumbent's advantage in advertiser relationships and targeting data.

## 4. Equilibrium Analysis

This section characterizes ad intensities and profits. All proofs are in the Appendix.

### 4.1 Ad-Free AI Is Not Sustainable

**Proposition 1 (No ad-free best response).** For any rival ad intensity, a\_j = 0 is never a best response for platform j ∈ {I, E}. A platform that offers ad-free AI answers earns AI profit −s·c·(its market share) < 0, and a small increase in ad intensity strictly increases its profit.

The intuition is direct. A list of links costs almost nothing to serve, so a search engine could give results away and sell the adjacent attention. An AI answer has a positive marginal cost, so an ad-free answer is a loss on every query. Some form of monetization is therefore necessary, and in a free-to-use service advertising is the instrument available. This formalizes the first stage of the dilemma described in the introduction: an incumbent that launches AI answers to retain users, without monetizing them, converts profitable legacy queries into loss-making ones.

### 4.2 Equilibrium Ad Intensity and Cost Pass-Through

**Proposition 2 (Equilibrium).** There is a unique interior equilibrium, with

```latex
a_I^{e} = \frac{t}{\gamma} + \frac{2c}{3m_I} + \frac{c}{3m_E}, \qquad a_E^{e} = \frac{t}{\gamma} + \frac{2c}{3m_E} + \frac{c}{3m_I}, \qquad \hat{x}^{e} = \frac{1}{2} + \frac{\gamma c}{6t}\left(\frac{1}{m_E} - \frac{1}{m_I}\right)
```

The incumbent's AI profit equals s·(2t·m\_I/γ)·(x̂^e)². In the symmetric case m\_I = m\_E = m:

- (a) Ad intensity is a^e = t/γ + c/m. It rises with differentiation t and inference cost c and falls with ad nuisance γ and ad productivity m.
- (b) Inference cost is fully passed through to users. Each additional dollar of inference cost per answer raises equilibrium ad revenue per answer by exactly one dollar, and equilibrium profit per platform, s·m·t/(2γ), does not depend on c.
- (c) With m\_I > m\_E, the incumbent sets a lower ad intensity than the entrant (a\_I^e < a\_E^e) and serves more than half of AI-amenable queries.

The term t/γ plays the role of the Hotelling markup, expressed in units of ad load rather than price. Part (b) is the central economic insight about generative AI. Users “pay” for inference with their attention: as answers become more compute-intensive, they become more ad-heavy, and platforms' margins are unchanged. Conversely, falling inference costs translate into fewer ads, not higher profit. Part (c) shows that an advantage in ad productivity works like a quality advantage. A platform that extracts more revenue per unit of ad exposure needs fewer ads to cover its costs, and so offers cleaner answers and wins share.

### 4.3 The Cost of an Ad-Free Rival

An AI-native entrant may commit to ad-free answers, for example to build trust or because it is financed by outside capital. Let m\_I = m\_E = m and suppose E sets a\_E = 0.

**Proposition 3 (Ad-free rival).** If E commits to a\_E = 0 and m·t > γ·c, the incumbent's best response is a\_I = t/(2γ) + c/(2m), its share of AI-amenable queries falls to 1/4 − γc/(4tm), and its AI profit is

```latex
\pi_I^{AI} = s\,\frac{(m t - \gamma c)^2}{8\gamma m t} = \frac{1}{4}\left(1 - \frac{\gamma c}{m t}\right)^2 \cdot s\,\frac{m t}{2\gamma}
```

That is, at most one quarter of its profit in the symmetric ad-supported equilibrium. The entrant loses s·c per user it serves and requires outside funding to sustain the commitment.

Proposition 3 has two implications. For the incumbent, an ad-free rival is far more damaging than an ad-supported one: it cuts AI profit by at least 75%. For the entrant, ad-free AI is a subsidized strategy whose cost grows with its own success. The model thus predicts that ad-free commitments by AI-native entrants are transitory, and that their abandonment raises incumbents' AI profits.

### 4.4 When Does Advertising Offset Search Cannibalization?

**Proposition 4 (Recovery threshold).** The incumbent's total profit changes with AI adoption at rate

```latex
\frac{d\Pi_I}{ds} = \pi_I^{AI}/s - R
```

(i) If AI answers are ad-free, the incumbent's profit falls strictly with s, and becomes negative as s approaches 1. (ii) In the symmetric ad-supported equilibrium, the incumbent's profit is non-decreasing in s if and only if

```latex
m \;\ge\; \bar{m} \equiv \frac{2\gamma R}{t}
```

Advertising in AI answers is therefore necessary but not sufficient to reverse the decline. The threshold rises with the profitability of legacy search R, because more is lost when each legacy query moves to AI. It also rises with ad nuisance γ and falls with differentiation t. Three levers follow for the incumbent: raise m by exploiting the richer intent contained in conversational queries; lower γ by keeping ads clearly separated from the answer; and raise t through ecosystem integration and defaults. The factor of 2 reflects competition: in the symmetric equilibrium the incumbent captures only half of AI-amenable queries, so its AI margin per query served must be twice the legacy profit per query.

### 4.5 Extension: The Advertiser Side

The base model fixes the price advertisers pay per unit of exposure. Platforms then interact only through consumers. In practice, advertisers allocate budgets across platforms, and new ad inventory from one platform lowers the price all platforms can charge. We now make the ad price endogenous.

**Setup.** Advertisers multi-home and treat ad exposures on search and AI platforms as substitutes, because they reach the same purchase intent. Consumers single-home, as before. Let ā be the number of ad units on a legacy results page. Total ad inventory per query is

```latex
A = (1 - s)\,\bar{a} + s\left[\hat{x}\,a_I + (1 - \hat{x})\,a_E\right]
```

and the market-clearing price per unit of exposure is m = μ − ηA, where μ > 0 is the level of advertiser demand and η ≥ 0 measures *advertiser-side crowding*: how much the price falls when inventory expands. The base model is the case η = 0. Let ε ≡ ηA/m denote the inverse elasticity of ad demand. Each platform takes m as given when it chooses ad intensity, because the digital ad market includes many sellers besides the two platforms. Legacy profit per query is now R = m·ā, so it moves with the ad price. Profits are

```latex
\Pi_I = (1 - s)\,m\bar{a} + s\,\hat{x}\,(m a_I - c), \qquad \Pi_E = s\,(1 - \hat{x})(m a_E - c)
```

We set m\_I = m\_E = m and study the symmetric equilibrium.

**Proposition 5 (Equilibrium with an advertiser side).** In the symmetric equilibrium, a = t/γ + c/m, and m is the larger root of

```latex
m^2 - B\,m + \eta s c = 0, \qquad B \equiv \mu - \eta\left[(1 - s)\bar{a} + s\,t/\gamma\right]
```

which exists if B² ≥ 4ηsc. Inference cost is no longer fully passed through: when η > 0, a higher c raises ad intensity on both platforms, which expands inventory and lowers the ad price (dm/dc = −ηs/√(B² − 4ηsc) < 0). The incumbent loses on both businesses: AI profit s·m·t/(2γ) falls, and legacy revenue (1 − s)mā falls too.

Proposition 2(b) is therefore the special case η = 0. With advertiser-side crowding, users bear part of the inference cost through more ads, and the advertising market bears the rest through a lower price, which also lowers the value of every legacy search ad.

**Proposition 6 (A rival's ads: two opposing effects).** Consider a small increase in the entrant's ad intensity, holding the incumbent's ad intensity fixed. Its effect on the incumbent's profit is

```latex
\frac{\partial \Pi_I}{\partial a_E} = s\Big[\underbrace{m\,\hat{x}}_{\text{consumer side}} \;-\; \underbrace{\eta\left((1-\hat{x}) + k(a_I - a_E)\right) V_I}_{\text{advertiser side}}\Big], \qquad V_I \equiv (1-s)\bar{a} + s\,\hat{x}\,a_I
```

where k = γ/(2t) and V\_I is the incumbent's ad inventory per query. At the symmetric equilibrium, the effect is positive if and only if

```latex
\varepsilon\,w_I < 1, \qquad w_I \equiv V_I / A
```

where w\_I is the incumbent's share of total ad inventory. On the consumer side, the rival's ads make it less attractive, and the incumbent keeps more users (the force behind Proposition 3). On the advertiser side, the rival's ads add inventory, the ad price falls, and the incumbent loses revenue on all of its inventory, legacy and AI. The second effect is larger when the incumbent owns more of the market's inventory. For a dominant search platform with w\_I close to 1, a rival's ads help only if ad demand is elastic (ε < 1). With unit-elastic demand they leave the incumbent about where it was.

**Proposition 7 (Scarcity dividend and the revised recovery threshold).** In the symmetric equilibrium, the incumbent's profit is Π\_I = m·Λ, with Λ ≡ (1 − s)ā + s·t/(2γ), and

```latex
\frac{d\Pi_I}{ds} = m\left(\frac{t}{2\gamma} - \bar{a}\right) + \Lambda\,\frac{\eta\,(\bar{a} - a)}{1 - \eta s c/m^2}
```

The first term is the base-model effect of Proposition 4 (it is non-negative if and only if m·t/(2γ) ≥ R). The second term is new. If an AI answer carries fewer ad units than a legacy results page (a < ā), the migration of queries to AI shrinks total inventory and raises the ad price, which partly offsets cannibalization. We call this the *scarcity dividend*. If AI answers carry more ads than legacy pages (a > ā), the term turns negative and the decline accelerates.

Proposition 7 refines the paper's main claim. Advertising in AI answers remains necessary (Proposition 1), but the profit-maximizing strategy for a dominant incumbent is ad-*light* AI. Each extra ad unit in an answer earns revenue, but it also lowers the price of every legacy search ad. A platform with a large share of inventory internalizes much of that loss, which an AI-native entrant does not.

### 4.6 Extension: Summaries or Answers? The Incumbent's Choice of Format

So far the incumbent served AI-amenable queries with AI answers. In practice, it chooses how to serve them, and it has moved in steps: Google added AI-generated summaries above its results (AI Overviews, 2024) before offering a full answer interface (AI Mode, 2025). The evidence in Section 2 shows why the step matters: summaries reduce organic clicks but not sponsored clicks (Agarwal and Sen 2026), whereas AI Mode lowered monetization (Section 5). We therefore let the incumbent choose a format for AI-amenable queries, holding m\_I = m\_E = m and η = 0.

**Formats.** The entrant always serves full AI answers. The incumbent chooses among three formats f:

Table 2. Formats available to the incumbent for AI-amenable queries.

| Format | Example | Quality gap to a full answer, g\_f | Incumbent's margin per query served |
| --- | --- | --- | --- |
| L: links only | Classic results page | Δ | R |
| H: summary above links | AI Overviews | Δ\_H = Δ − Δ\_O | R − c\_O |
| A: full AI answer | AI Mode | 0 | m a\_I − c (chosen ad intensity) |

Here Δ > 0 is how much users prefer a full answer to a list of links, Δ\_O ∈ (0, Δ) is the part of that gap a summary closes, and c\_O < R is the inference cost of a summary. In formats L and H, the incumbent keeps its results-page ads, so its margin is R or R − c\_O, consistent with sponsored clicks being unaffected by summaries. A user at x obtains v − g\_f − tx from the incumbent under L or H, and v − γa\_E − t(1 − x) from the entrant.

**Lemma.** Under a format with fixed margin r and quality gap g, the entrant's best response and the incumbent's share are

```latex
a_E = \frac{t + g}{2\gamma} + \frac{c}{2m}, \qquad \hat{x}(g) = \frac{3t - g}{4t} + \frac{\gamma c}{4tm}, \qquad \pi_I = s\,r\,\hat{x}(g)
```

The entrant shows more ads when the incumbent's format is worse (larger g), because it faces less competitive pressure. Under format A, the symmetric equilibrium of Proposition 2 applies, with π\_I = s·m·t/(2γ).

**Proposition 8 (Summaries first, answers later).** (i) Summaries dominate links if and only if

```latex
R\,\Delta_O > c_O\left(3t - \Delta + \Delta_O + \gamma c/m\right)
```

which holds whenever summaries are cheap relative to the quality they add. (ii) Full answers dominate summaries if and only if the remaining quality gap exceeds a threshold:

```latex
\Delta_H \ge \Delta_H^{*} \equiv 3t + \frac{\gamma c}{m} - \frac{2mt^2}{\gamma\,(R - c_O)}
```

(iii) The threshold rises with legacy profitability R and inference cost c, and falls with ad productivity in AI answers m and with the cost of summaries c\_O.

As AI answers improve relative to summaries (Δ\_H rises over time), the incumbent first adopts summaries, which defend its users without touching its ad revenue, and switches to full answers only when the remaining gap becomes large enough. The switch comes later the more profitable legacy search is, which is the innovator's dilemma in a precise form: the incumbent delays the format that cannibalizes its clicks in proportion to what those clicks earn. Better monetization of AI answers (higher m) brings the switch forward.

**Corollary (Defensive answering).** The incumbent may switch to full answers even when doing so leaves its profit below the pre-AI level, that is, when Δ\_H ≥ Δ\_H\* but m·t/(2γ) < R. In that region, answering is not a way to restore profit but to limit its loss: under summaries, the entrant's better answers would take a growing share of users.

The corollary separates two questions that the base model combined. Proposition 4 asks whether AI answers restore the pre-AI profit; Proposition 8 asks whether they beat the alternative formats available today. An incumbent can rationally launch full AI answers that lower its profit, and the market can rationally reprice it when it does, as the events of 2026 illustrate. The extension also locates the costs. Under summaries, publishers bear the loss of organic clicks while the incumbent's ad revenue is protected; under full answers, the incumbent's own monetization falls as well.

### 4.7 Extension: Scale, Capability, and the Timing of Full Answers

Proposition 8 compares profits per query and ignores the cost of being able to offer full answers at all: building or licensing a model, serving infrastructure, and safety work. Section 5.6 shows that this matters, because small search engines with little legacy profit did not move early. We add a fixed cost and let engines differ in scale.

**Setup.** Search engine j handles a share σ\_j ∈ (0, 1) of queries in its market, and its legacy profit per query rises with its position, R(σ) = R\_0 + R\_1σ with R\_1 > 0 (larger engines have deeper ad auctions). It currently serves AI-amenable queries with summaries (format H). Moving to full answers costs a fixed amount K\_j per period, which is lower for engines with an in-house frontier model. Answer quality improves over calendar time d, so the remaining gap Δ\_H(d) rises and the incumbent's share under summaries, x̂\_H(d) ≡ x̂(Δ\_H(d)) from the Lemma in Section 4.6, falls. Let π\_A = m t/(2γ) denote the profit per AI-amenable query under full answers. Engine j switches at the first date d at which

```latex
\sigma_j\left[\pi_A - \big(R(\sigma_j) - c_O\big)\,\hat{x}_H(d)\right] \;\ge\; K_j
```

The bracket is the gain per query, which falls with legacy profit; the factor σ\_j scales it by the engine's volume, against which the fixed cost is spread.

**Proposition 9 (Mid-sized engines move first).** Let D(σ, K) be the switching date. (i) D is quasi-convex in σ: at any date d, the engines that have switched form an interval of shares \[σ\_L(d), σ\_H(d)\], which widens over time. The first engines to switch have intermediate shares; small engines switch later because they lack scale, and large engines switch later because they lose more legacy profit. (ii) D is increasing in K, so engines with in-house models switch earlier at every share. (iii) An engine for which σ\[π\_A − (R(σ) − c\_O)x̂\_H(d)\] < K at every date never switches unless K falls, for example when open or licensable models become cheaper.

Proposition 9 replaces the monotone prediction of Proposition 8 with an inverted-U relation between scale and the speed of adoption, and adds capability as a separate determinant. It also explains why the smallest legacy engines adopted full answers mainly in 2025–2026, when licensable models became cheaper. AI-native entrants lie outside the model: they have no legacy business and incurred the fixed cost as the price of entry. In a numerical example (π\_A = 1, R\_0 = 0.6, R\_1 = 1.2, c\_O = 0.05, K = 0.04, x̂\_H(d) = 0.3 + 0.9e^(−0.05d)), the first engine to switch has a share of 0.18; engines with shares of 0.10, 0.30, 0.60, and 0.90 switch after 8.3, 6.4, 14.6, and 22.9 periods; and an engine with a share of 0.02 never switches.

### 4.8 Extension: User Trust and the Decision to Click

The model so far treats the fall in clicks as given: an AI answer replaces the results page, and users do not click. A natural explanation is that users trust AI answers and see no need to check them. We model that trust explicitly, let it be learned, and ask when trust, rather than effort, explains the decline in clicks.

**Setup.** An AI answer is correct with probability q, its true accuracy. A user's trust θ is the accuracy the user believes the answer has. Each query carries a stake L, the user's loss from acting on a wrong answer, drawn from a distribution F across queries and users. Clicking through to sources to verify the answer costs effort e > 0 and reveals any error. A user clicks if and only if the expected loss avoided exceeds the effort:

```latex
(1 - \theta)\,L > e \quad\Longrightarrow\quad \omega = G(\theta) \equiv 1 - F\!\left(\frac{e}{1 - \theta}\right)
```

where ω is the share of answers that users verify. G is decreasing: more trust, fewer clicks. Clicks also fall when effort rises or stakes are low, whatever the level of trust.

**Learning.** Users learn about accuracy from the errors they detect. An error is detected for sure when the user verifies, and only with probability ζ otherwise, for example when its consequences become visible. We assume users treat the absence of a detected error as evidence of a correct answer (“no news is good news”), a pattern documented as automation bias. Their long-run trust is then

```latex
\theta = T(\omega) \equiv 1 - (1 - q)\left[\zeta + (1 - \zeta)\,\omega\right]
```

Trust and clicking are jointly determined: an equilibrium is a pair (θ, ω) with ω = G(θ) and θ = T(ω), that is, a fixed point of Φ(θ) ≡ T(G(θ)).

**Proposition 10 (Trust traps).** (i) An equilibrium exists, and in every equilibrium users overtrust AI answers: θ − q = (1 − q)(1 − ζ)(1 − ω) ≥ 0, with more overtrust the fewer users click. (ii) If Φ crosses the 45-degree line from below at some point, there are at least three equilibria: a *vigilant* one, with low trust and many clicks; a *complacent* one, with high trust and few clicks; and an unstable one between them. (iii) If AI answers are accurate enough that e/(1 − q) exceeds the largest stake, the complacent equilibrium is unique. (iv) With multiple equilibria, a temporary rise in the detection of errors, such as widely publicized AI mistakes, can move users permanently from the complacent to the vigilant equilibrium.

In a numerical example with stakes drawn from a log-normal distribution (median 0.35, dispersion parameter 0.2), e = 0.05 and ζ = 0.02, an AI with accuracy q = 0.6 supports three equilibria: users verify every answer (θ = 0.60), verify 31% of them (θ = 0.87, unstable), or verify almost none (θ = 0.99, overtrust of 39 points). With q = 0.9, only the complacent equilibrium remains, with overtrust of 10 points. Raising ζ to 0.5 for a period moves users from the complacent to the vigilant equilibrium, where they stay after ζ returns to 0.02.

**Trust or effort?** The model separates the two explanations by the stakes of the query. Low trust raises clicks only where stakes are high enough to justify the effort; for low-stakes queries users do not click whatever they believe. Three implications follow, each consistent with existing evidence.

1. *Clicks fall most for low-stakes queries.* In the field experiment of Agarwal and Sen (2026), the effect of AI Overviews on clicks came from informational queries. Across six countries, users report trusting AI answers less and checking them more often for health and politics than for other topics ([Simon, Nielsen, and Fletcher 2025](https://mediawell.ssrc.org/citations/generative-ai-and-news-report-2025-how-people-think-about-ais-role-in-journalism-and-society/)).
2. *Distrust does not imply clicking.* In a 2025 U.S. survey, 82% of respondents described themselves as skeptical of AI answers, but only about 8% always check the sources ([Exploding Topics 2025](https://explodingtopics.com/blog/ai-trust-gap-research)). Much of the decline in clicks therefore reflects low stakes and effort, not only trust.
3. *Salient errors raise clicks if trust drives clicking.* Part (iv) predicts that publicized failures, such as the widely shared AI Overviews errors of late May 2024 that led Google to restrict the feature ([Engadget 2024](https://www.engadget.com/google-is-putting-more-restrictions-on-ai-overviews-after-it-told-people-to-put-glue-on-pizza-011316780.html)), should raise verification clicks, and keep them higher if users were in a complacent equilibrium. Section 5.7 tests this prediction.

**Effort, not trust, as the main driver.** The evidence above suggests that effort explains more of the shift than trust. A simple choice rule makes the point. A user facing a question can read search results, at effort e\_S and with accuracy q\_S, or read an AI answer, at effort e\_A < e\_S and with perceived accuracy θ. With benefit B from a correct answer, the user chooses the AI answer if

```latex
e_S - e_A \;>\; (q_S - \tau)\,B
```

The user prefers the AI answer whenever the effort it saves exceeds the expected cost of its lower accuracy. Even a user who trusts AI answers less than search results (θ < q\_S) chooses them for low-stakes questions; trust matters only when B is large. This rule implies that a pure trust shock, which lowers θ while leaving effort unchanged, should move users back to search results only for high-stakes questions, and should leave aggregate clicks largely unchanged. Section 5.7 tests this implication against the trust account.

**Trust and advertising.** The trust model also gives a foundation for ad nuisance γ in Section 3. If users discount the accuracy of answers that carry ads, trust falls to T(ω) − κa for ad intensity a, with κ > 0, so more users verify and the answer is worth less to them. Ads in answers therefore raise outbound clicks, which benefits publishers, and lower the value of the answer, which is the cost γ captures. A platform that prefers users to stay on its answer page also prefers the complacent equilibrium, which raises a consumer-protection concern: complacent users overtrust most. Clear labeling of ads and visible sourcing, by raising ζ, push users toward calibrated trust.

## 5. Empirical Analysis

The empirical analysis proceeds in four steps. Section 5.1 examines the premise that people who use AI more come to rely less on search. Sections 5.2 to 5.5 test the monetization predictions using daily stock returns around AI-related news, quarterly segment revenue from Alphabet's and Meta's filings for 2019Q4 to 2026Q3, and Alphabet's reported paid clicks and cost per click. Section 5.6 turns to the timing predictions of Propositions 8 and 9, first across 17 search engines and then within Google across 47 countries. Section 5.7 uses the AI Overviews errors of May 2024 to ask whether trust or effort explains why users stop clicking. Section 5.8 brings the results together.

Two findings frame what follows. The premise survives only in a narrower form than the one we started with: AI reduces the clicks that follow a search, but we find no evidence that it reduces the number of searches. And while news that AI is displacing search lowers Alphabet's market value without moving Meta's, the evidence on the monetization side of the model is weaker, and the prediction of Proposition 3 is not supported.

### 5.1 First Stage: Does AI Use Reduce Search Use?

The model's premise is that queries migrate from link-based search to AI answers as AI improves (s rises). The broad claim that people who use AI more use search engines less is not supported by our data. A narrower claim is: AI reduces the clicks that follow a search. We draw this conclusion from published evidence (Table 3) and three new tests (Table 4).

**Published evidence.**

Table 3. Published evidence on AI and search behavior.

| Source | Data | Finding | What it measures |
| --- | --- | --- | --- |
| [Chapekis (2025), Pew Research Center](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/) | Browsing data of 900 U.S. adults, March 2025; 68,879 Google searches | A traditional result was clicked on 8% of visits to pages with an AI summary vs. 15% without; sessions ended on 26% vs. 16% | Clicks per search |
| [del Rio-Chanona et al. (2024)](https://kti.krtk.hu/en/publikacio/r-maria-del-rio-chanona-nadzeya-laurentsyeva-johannes-wachss-article-in-the-pnas-nexus-2024/) | Stack Overflow vs. Russian and Chinese Q&A sites and math forums | Activity fell 25% within six months of ChatGPT's release, relative to controls | Substitution of AI for web Q&A |
| [Apple testimony (Fortune 2025)](https://fortune.com/2025/05/08/apple-eddy-cue-testimony-google-alphabet-safari-ai-search-features) | Safari search volume | Fell in April 2025 for the first time in about 22 years; Google disputes the claim | Search volume, one channel |
| [Wikimedia Foundation (TechCrunch 2025)](https://techcrunch.com/2025/10/18/wikipedia-says-traffic-is-falling-due-to-ai-search-summaries-and-social-video) | Wikipedia human pageviews | −8% year over year in 2025, after a bot-detection update; attributed to AI summaries and social video | Visits referred by search |
| [Alphabet (MarketBeat 2026)](https://www.marketbeat.com/instant-alerts/transcript-alphabet-q3-earnings-call-highlights-2026-10-29/) | Google search queries | Year-over-year query growth highest in five years (Q3 2026) | Search volume, Google |

The evidence divides by what is measured. Measures of clicks and of visits to destinations that search used to supply all decline. Measures of search volume are mixed: one channel (Safari) declined and individual chatbot adopters search less (Padilla et al. 2026), but Google's total queries are growing. Table 1 in Section 2 lists further studies.

**Test A: U.S. states, Google Trends.** We collected monthly Google Trends series for 51 states (including the District of Columbia), January 2019 to September 2026. The outcome is the log share of question-type queries that AI can answer (“how to,” “what is”) relative to queries it cannot easily replace (“weather,” “near me”). Treatment is a state's search intensity for ChatGPT in 2023–2026, standardized, interacted with a post-December 2022 indicator. We include state and month fixed effects and cluster standard errors by state. If AI substitutes for informational search, high-adoption states should show a relative decline in question-type queries.

**Test B: European Wikipedia editions and official AI-use statistics.** Most Wikipedia visits arrive from search engines, so pageviews proxy for clicks out of search. We measure AI adoption with Eurostat's 2025 survey of ICT use by individuals: the share of people aged 16–74 who used generative AI tools in the last three months ([Eurostat 2026](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/edn-20260210-1); table isoc\_ai\_iaiu). Rates range from 17% in Türkiye and 18% in Romania to 48% in Denmark and 56% in Norway. We match 24 Wikipedia editions whose readers are concentrated in one Eurostat country (for example, Danish to Denmark, Hungarian to Hungary); we exclude the Spanish, Portuguese, and English editions because most of their readers are outside Europe. Pageviews come from Wikimedia's hourly project-level dumps (four sampled hours per month, January 2019 to September 2026). We include edition and month fixed effects, cluster by edition, and in one specification control for each country's 2022 share of daily internet users (Eurostat isoc\_ci\_ifp\_fu) interacted with the post period, because AI adoption tracks general digitalization. Eurostat's measure is official and survey-based, which addresses the main weakness of search-interest indices, but it is available only for 2025, so treatment intensity is cross-sectional. As a robustness check, we repeat the analysis for 22 editions worldwide using Google Trends interest in the ChatGPT topic.

**Test C: Natural experiment from the staggered launch of AI Overviews.** Tests A and B compare places by how much they use AI, which is not randomly assigned. Google's AI Overviews, by contrast, reached different language markets at different times, for reasons unrelated to local search trends: the United States in May 2024 ([Google 2024a](https://blog.google/products/search/ai-overviews-search-october-2024/)); the United Kingdom, India, Japan, Indonesia, Mexico, and Brazil in August 2024 ([Android Authority 2024](https://androidauthority.com/google-ai-overviews-expansion-3494705)); nine European countries including Germany, Italy, Spain, and Poland on March 26, 2025 ([PPC Land 2025](https://ppc.land/google-expands-ai-overviews-to-more-european-markets/)); more than 40 languages on May 20, 2025 ([Google 2025](https://blog.google/products/search/ai-overview-expansion-may-2025-update/)a); and France on July 22, 2026 ([PPC Land 2026](https://ppc.land/google-ends-france-ai-overviews-blackout-as-68-users-flagged-the-gap/)b). An AI Overview answers the query on the results page, so it should reduce clicks to sources such as Wikipedia. Khosravi and Yoganarasimhan (2026) use a related design, comparing English Wikipedia articles with their German and French counterparts, and estimate a reduction of about 5% in search referrals. Our version differs in using 25 editions and several rollout cohorts, and in separating desktop from mobile traffic; it therefore serves as a replication and extension rather than a new design. We assign each of 25 Wikipedia editions the first full month in which AI Overviews served its language in its main market: English (June 2024); Japanese, Indonesian, Portuguese, Spanish, and Hindi (September 2024); German, Italian, and Polish (April 2025); French (August 2026). Editions in languages added only in May 2025 (Korean, Dutch, Swedish, Czech, Turkish, Vietnamese, Thai, Hebrew, Arabic, Chinese, Ukrainian, Russian, Malay, Bengali) serve as not-yet-treated controls through April 2025; Persian is never treated. We estimate group-time effects with the Callaway and Sant'Anna (2021) estimator, using not-yet-treated editions as controls and bootstrapping over editions (499 draws). We focus on the August 2024 cohort, the only one with a large control group (19 editions) throughout its window.

Table 4. AI adoption and search-related activity. Coefficient on adoption × post (standard error clustered by state or edition; p-value).

| Test | Specification | Estimate | Reading |
| --- | --- | --- | --- |
| A. U.S. states (N = 4,743) | Question-type vs. other queries | +0.024 (0.004; p < 0.01) | Wrong sign; driven by “near me” and “weather” falling in high-adoption states |
| A | “how to” only | −0.004 (p = 0.08) | Negligible |
| A | “what is” only | −0.001 (p = 0.69) | None |
| B. 24 European editions, Eurostat AI use (N = 2,232) | Difference-in-differences, all platforms | −0.063 (0.041; p = 0.13) | Not significant |
| B | Adding daily internet use × post (N = 2,139) | −0.036 (0.066; p = 0.59) | Disappears |
| B | Desktop only | −0.033 (0.027; p = 0.23) | Not significant |
| B | Sample before bot reclassification (to April 2025) | −0.085 (0.042; p = 0.04) | Significant only in this window |
| B | By year, relative to 2022 | 2023: −0.044 (p < 0.01); 2024: −0.015 (p = 0.15); 2025: +0.011 (p = 0.52); 2026: +0.043 (p = 0.04) | Short-lived dip in 2023, then reversal |
| B | Long difference, 2021–22 to 2025–26 (N = 24) | +0.30 pp per point of AI use (p = 0.09) | Wrong sign: high-adoption countries lost slightly less traffic |
| B | Long difference with daily internet use | +0.25 (p = 0.37) | None |
| B (robustness). 22 editions worldwide, Google Trends index | Difference-in-differences | −0.090 (0.034; p < 0.01) | Supportive at face value |
| B (robustness) | Pre-ChatGPT trend gap (per month) | −0.0071 (0.0021; p < 0.01) | Driven by a trend that predates ChatGPT |
| B (robustness) | With edition-specific trends | +0.090 (0.037; p = 0.01) | Wrong sign |
| C. AI Overviews launch, Aug. 2024 cohort (25 editions) | All platforms, months 0 to +6 | +0.022 (0.046; 95% CI −0.072 to 0.109) | No effect on total views |
| C | Desktop | −0.089 (0.046; 95% CI −0.177 to −0.000) | About 9% fewer desktop views; pre-period average −0.012 |
| C | Mobile web | +0.062 (0.058) | None; pre-period average +0.111 indicates a pre-trend |
| C | Desktop, excluding Portuguese | −0.061 (0.040; 95% CI −0.142 to 0.018) | Same sign, not significant |
| C | Desktop, excluding Hindi | −0.090 (0.054; 95% CI −0.193 to 0.010) | Same sign, not significant |
| C | Desktop, all cohorts pooled | −0.047 (0.046) | Same sign, not significant |

&#91;embedded content: Wikimedia hourly projectviews dumps (four sampled hours per month); launch dates from Google and trade press; Callaway–Sant'Anna estimator with not-yet-treated controls\]

Figure 1 shows the event study for the August 2024 cohort. Desktop estimates fluctuate around zero before launch and are negative in all seven months after it, although most individual intervals include zero. Total views, which are dominated by mobile, show no change.

**Results.** Tests A and B find no evidence that places adopting AI more intensively reduced search-related activity more. In Test A the estimate has the wrong sign: in high-adoption states, the comparison queries fell, while question-type queries hardly changed. In Test B, using Eurostat's official measure, the difference-in-differences estimate is negative but not significant, and it shrinks further once general internet use is controlled for. Editions in high-adoption countries dipped briefly in 2023, but the gap closed by 2025 and reversed in 2026; over the full period, high-adoption countries lost slightly less traffic. The worldwide robustness sample looks supportive at first, but the effect reflects a trend that predates ChatGPT. Test C, the natural experiment, gives the closest evidence for the narrow premise. Launching AI Overviews in a market reduced desktop Wikipedia views by about 9%, with no pre-trend. However, the estimate is at the edge of significance, it loses significance when single editions are dropped, and total views did not change.

**Interpretation.** The data support a narrower premise: AI reduces the clicks that follow a search, rather than the number of searches. Users still query Google, increasingly through AI Overviews and AI Mode, but click less (Chapekis 2025), and the staggered launch of AI Overviews was followed by a fall of about 9% in desktop Wikipedia views (Test C). Google's paid-click growth slowed to 2–4% in 2025 even as queries grew (Section 5.5). In the model, this is the case in which AI-amenable queries stay on the incumbent's platform but are answered by AI. That is the channel through which revenue per query falls, and Propositions 4–7 need only this. We therefore restate the premise as follows: *as AI use rises, a growing share of queries is resolved without a click on a link.* This premise is compatible with individual-level evidence that chatbot adopters search less (Padilla et al. 2026); our aggregate tests may miss that effect because adopters were a minority and because queries in AI Mode still count as searches. Field-experimental evidence also shows that AI Overviews reduce organic clicks but not sponsored clicks (Agarwal and Sen 2026). The loss of revenue per search therefore arises mainly where AI answers replace the results page, as in AI Mode and chatbots, which is consistent with Alphabet's attribution of its slowdown to AI Mode.

**Limitations.** Google Trends measures shares of searches, not volumes, so Test A cannot detect a fall in total search. Adoption is measured cross-sectionally: Eurostat asked about generative AI for the first time in 2025, and search-interest measures correlate with urbanization and income. Test B has 24 clusters, and its pre-2025 data include bots later reclassified. A direct test of the broad claim requires user-level panel data linking AI use to search sessions, which is not publicly available.

### 5.2 Event Study

**Design.** We use daily adjusted closing prices for Alphabet (GOOGL), Meta (META), and the S&P 500 ETF (SPY) from Yahoo Finance. For each event, we estimate a market model on trading days \[−280, −31\] and compute the cumulative abnormal return (CAR) over \[0, +1\]. Meta serves as a control: it sells digital advertising but does not depend on search, so a search-specific shock should move Alphabet and not Meta. We classify events ex ante. *Substitution* events signal that AI displaces search (Proposition 4 predicts a negative CAR for Alphabet). *Monetization* events signal that advertising enters AI answers, by Google itself (Propositions 1–2) or by an AI-native rival (Proposition 3); both predict a positive CAR. A capital-expenditure announcement serves as a cost-shock comparison.

Table 5. Abnormal returns around AI events, CAR\[0, +1\] in % (t-statistic in parentheses). Newest first.

| Event day | Event | Type | Predicted sign (GOOGL) | GOOGL | META | GOOGL − META |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-29 | Alphabet Q3 results; management cites “lower monetization” of AI Mode | Substitution | − | −12.59 (−5.44) | +3.79 (1.19) | −16.38 |
| 2026-07-23 | Alphabet Q2 results; 2026 capex guidance raised | Cost shock | − | −5.62 (−2.60) | −3.21 (−1.16) | −2.41 |
| 2026-02-09 | ChatGPT ads go live (U.S.) | Monetization (rival) | + | −1.94 (−0.83) | +1.18 (0.50) | −3.12 |
| 2026-01-16 | [OpenAI announces ad test in ChatGPT](https://www.bloomberg.com/news/articles/2026-01-16/openai-to-test-targeted-ads-in-chatgpt-stepping-up-revenue-push) | Monetization (rival) | + | −0.37 (−0.15) | −0.07 (−0.03) | −0.30 |
| 2025-05-21 | [Google Marketing Live: ads in AI Mode, AI Overviews ads on desktop](https://blog.google/products/ads-commerce/google-marketing-live-2025/) | Monetization (own) | + | +6.01 (2.86) | +2.18 (0.95) | +3.83 |
| 2025-05-07 | Apple executive testifies that Safari searches fell for the first time | Substitution | − | −7.01 (−3.34) | +0.35 (0.15) | −7.36 |
| 2024-05-21 | Google Marketing Live: ads coming to AI Overviews | Monetization (own) | + | −0.26 (−0.13) | −0.45 (−0.18) | +0.18 |
| 2022-11-30 | ChatGPT released | Substitution | − | +2.17 (1.30) | +4.71 (1.27) | −2.54 |

**Results.** Substitution news is priced as a search-specific shock. The two events that revealed actual displacement, falling Safari searches and weaker AI Mode monetization, produced Alphabet CARs of −7.0% and −12.6% (both p < 0.001), while Meta's CARs were small and insignificant. Across the three substitution events, the pooled standardized CAR for Alphabet is Z = −4.32 (mean CAR −5.8%). The release of ChatGPT itself produced no immediate reaction, consistent with investors learning about substitution only as usage data accumulated.

The monetization evidence is mixed. Google's announcement of ads in AI Mode was followed by a +6.0% CAR (t = 2.86), and +3.8 points relative to Meta. The 2024 announcement of ads in AI Overviews produced no reaction. Across the four monetization events, the pooled Z is 0.88 (mean +0.9%), not significant. The October 2026 decline also contains a cost component: the July 2026 capex announcement alone produced a −5.6% CAR. The decline is therefore not entirely attributable to substitution.

### 5.3 Quarterly Evidence: Search Revenue and the Advertising Cycle

**Data.** We collected quarterly “Google Search & other” revenue from all of Alphabet's earnings releases filed with the SEC (Form 8-K, Exhibit 99.1), and Meta's quarterly revenue from its XBRL filings. Meta's revenue, about 98% advertising, serves as a benchmark for the digital advertising cycle. The sample covers 28 quarters of year-over-year growth, 2019Q4–2026Q3; 13 precede ChatGPT and 15 follow it.

&#91;embedded content: Alphabet and Meta 8-K earnings releases and XBRL filings (SEC EDGAR), 2018Q4–2026Q3; growth = 100 × log difference over four quarters\]

Figure 2 shows the two growth series. Before ChatGPT, Search growth swung with the advertising cycle, apart from 2021Q3–2022Q4, when Apple's App Tracking Transparency (ATT) depressed Meta specifically. After ChatGPT, both series recover, but Search rises much less than Meta in the 2023–2026 upswing. Regressions in Section 5.4 quantify this pattern.

### 5.4 Regressions and Placebo Tests

We estimate

```latex
g^{S}_t = \alpha + \beta\, g^{M}_t + \beta_{post}\,(g^{M}_t \times Post_t) + \delta\, Post_t + \theta\, k_t + \lambda_1 ATT_t + \lambda_2 COVID_t + \varepsilon_t
```

where g^S and g^M are the year-over-year growth of Search and Meta revenue, Post = 1 from 2023Q1, k counts quarters since 2022Q4 in the post period, ATT = 1 for 2021Q3–2022Q4, and COVID = 1 for 2020Q2–2021Q2. Standard errors are Newey–West with four lags.

Table 6. Search revenue growth and the advertising cycle, 2019Q4–2026Q3 (N = 28). Coefficients with HAC standard errors in parentheses.

| Variable | (1) Level shift | (2) Post-ChatGPT trend | (3) Sensitivity break |
| --- | --- | --- | --- |
| Meta growth g^M | 1.109\*\*\* (0.129) | 1.159\*\*\* (0.121) | 1.273\*\*\* (0.117) |
| g^M × Post |  |  | −0.681\*\*\* (0.119) |
| Post | −0.651 (0.913) | 2.947 (2.343) | 12.549\*\*\* (2.291) |
| Quarters since ChatGPT, k |  | −0.452\*\* (0.223) |  |
| ATT | 18.464\*\*\* (1.877) | 19.049\*\*\* (1.728) | 20.384\*\*\* (2.015) |
| COVID | −3.937 (3.416) | −4.394 (3.233) | −5.440\* (2.880) |
| Constant | −9.395\*\*\* (2.480) | −10.352\*\*\* (2.323) | −12.538\*\*\* (2.233) |
| R² | 0.83 | 0.84 | 0.88 |

Note. \*\*\* p < 0.01, \*\* p < 0.05, \* p < 0.10.

Taken at face value, columns (2) and (3) support the model. After ChatGPT, Search growth falls behind the advertising cycle by about 0.45 points per quarter, and its sensitivity to the cycle drops from 1.27 to 0.59. Search revenue participates in only about half of an advertising upswing.

Placebo tests do not support a causal reading. We re-estimate both specifications with break dates from 2021Q1 to 2024Q3.

Table 7. Placebo break dates. Coefficient (p-value).

| Break date | Trend k, spec. (2) | g^M × Post, spec. (3) | AIC, spec. (3) |
| --- | --- | --- | --- |
| 2021Q1 (placebo) | −0.510 (<0.01) | −0.366 (0.07) | 176.3 |
| 2021Q3 (placebo) |  | −0.748 (<0.01) | 163.0 |
| 2022Q1 (placebo) | −0.646 (0.04) | −0.749 (<0.01) | 166.9 |
| 2023Q1 (ChatGPT) | −0.452 (0.04) | −0.681 (<0.01) | 169.5 |
| 2023Q3 | −0.127 (0.54) | −0.695 (<0.01) | 173.5 |
| 2024Q1 | −0.370 (0.11) | −0.659 (<0.01) | 176.1 |

Breaks placed before ChatGPT fit as well or better; the best fit (lowest AIC) is 2021Q3, the start of the ATT shock to Meta. Without the ATT and COVID controls, the sensitivity break is not significant (−0.18, p = 0.19). If ATT quarters are dropped instead of controlled for, it remains significant (−1.01, p < 0.01, N = 22). We conclude that quarterly firm-level data are consistent with weaker Search growth since 2023 but cannot attribute it to AI. Meta is an imperfect benchmark: its own shocks (ATT, and later AI-driven ad tools) move the comparison. Identification requires the cross-sectional designs in Section 5.8.

### 5.5 Advertiser-Side Evidence: Paid Clicks and Cost-per-Click

Propositions 6 and 7 rest on advertiser-side crowding (η > 0): the price of a search ad should rise when inventory grows more slowly and fall when it grows faster, holding advertiser demand fixed. Alphabet reports the year-over-year change in paid clicks and in cost-per-click (CPC) for Google Search & other in each Form 10-Q. We collected these for the first three quarters of 2021–2026 (N = 18; fourth quarters are reported only on an annual basis).

&#91;embedded content: Alphabet Forms 10-Q, “Monetization Metrics,” three months ended March, June, and September, 2023–2026 (SEC EDGAR)\]

Figure 3 shows the post-ChatGPT period. In 2024–2025, paid-click growth slowed to 2–7% while CPC growth held at 7–8%. In 2026, as AI Mode ads expanded, click growth rose to 13% and CPC growth fell to 3–5%.

Table 8. CPC growth regressed on paid-click growth, controlling for advertiser demand (Meta revenue growth). HAC standard errors (two lags) in parentheses.

| Variable | (1) 2021–2026 | (2) 2021–2026 | (3) 2023–2026 |
| --- | --- | --- | --- |
| Paid-click growth | 0.133 (0.282) | −0.750\*\*\* (0.263) | −1.020\*\*\* (0.100) |
| Meta revenue growth | 0.355\*\*\* (0.083) | 0.570\*\*\* (0.064) | 0.538\*\*\* (0.024) |
| Post-2023 |  | −12.142\*\*\* (3.207) |  |
| N | 18 | 18 | 12 |
| R² | 0.53 | 0.64 | 0.94 |

Note. \*\*\* p < 0.01.

Once the 2021–2022 period is separated out, CPC growth falls almost one-for-one with paid-click growth (−1.02 in column 3). This is consistent with η > 0 and an inverse demand elasticity ε close to 1. Combined with Proposition 6, it gives a reason for the null result in Section 5.2. Google holds most search ad inventory (w\_I close to 1), so ε·w\_I is close to 1. The consumer-side gain from ChatGPT's ads and the advertiser-side loss then roughly cancel. The same estimate supports the scarcity dividend of Proposition 7: when AI answers reduced click growth in 2024–2025, higher prices kept Search revenue growing at 11–14%.

Two caveats apply. First, a coefficient near −1 is also what fixed advertiser budgets would produce mechanically, since revenue is clicks times CPC. That reading is itself an advertiser-side mechanism, but it means the estimate cannot distinguish crowding from budget constraints. Second, the sample is small and the post-2023 relationship does not hold when 2022 is included (coefficient −0.13, p = 0.75).

### 5.6 Out-of-Sample Test: Bing

Proposition 8 implies that a search engine with little legacy search profit has a low threshold for full AI answers and should adopt them early, without the summary step. Relative to Google, Bing is such a firm, although its absolute legacy revenue is large (Table 13). In January–March 2026, Microsoft's search advertising revenue was $3.8 billion ([Microsoft 2026](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=10-Q)), against $60.4 billion for Google Search & other ([Alphabet 2026c](https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000043/googexhibit991q12026.htm)), about one-sixteenth. We test three implications.

**Order of formats.** Microsoft announced a chat-based Bing with full AI answers on February 7, 2023, and announced ads inside chat answers on March 29, 2023 ([Engadget 2023](https://autos.yahoo.com/microsoft-reveals-how-its-putting-ads-in-bings-ai-chatbot-052014029.html)). Google launched AI summaries in the United States in May 2024 and full AI answers (AI Mode) in May 2025. As Proposition 8 predicts for a firm whose legacy profit was small relative to its rival's, Bing went straight to full answers, 15 months before the incumbent's summaries and 27 months before its full answers; the incumbent took the summary step first.

**Market share.** In the model, a rival's full answers draw users away from an incumbent that offers only links, and the incumbent's summaries close part of that gap. Bing's share should therefore rise faster after February 2023 and stop rising once Google adds summaries. We estimate a segmented trend model of Bing's monthly share from StatCounter, January 2019 to August 2026 (N = 92), with breaks at Bing Chat (February 2023), AI Overviews (June 2024), and AI Mode (June 2025), and Newey–West standard errors. Figure 4 plots both series.

&#91;embedded content: StatCounter Global Stats, search engine market share, January 2019–August 2026; September 2026 excluded as an outlier (worldwide desktop 14.65%)\]

Table 9. Bing's share trend, percentage points per month, by period.

| Period | Worldwide desktop | United States, all devices |
| --- | --- | --- |
| Before Bing Chat (2019–Jan. 2023) | +0.10 | +0.02 |
| After Bing Chat, before AI Overviews | +0.26 (change +0.16, p < 0.01) | +0.14 (change +0.12, p < 0.01) |
| After AI Overviews, before AI Mode | +0.02 (change −0.24, p < 0.01) | +0.03 (change −0.11, p < 0.01); level −1.27 (p < 0.01) |
| After AI Mode | −0.16 (change −0.18, p < 0.01) | +0.11 (change +0.08, p = 0.21) |

The worldwide desktop pattern matches the prediction: Bing's gains accelerated after it alone offered full answers, stopped once Google added summaries, and reversed after Google launched full answers. In the United States, Bing's share also rose faster after Bing Chat and fell when AI Overviews launched, but it rose again after AI Mode, which the model does not predict.

**Revenue and market value.** Two further tests are uninformative. Microsoft's search advertising revenue growth (excluding traffic acquisition costs) exceeded Google's search growth by 2.9 points on average before 2023 and by 1.3 points after, a difference that is not significant (p = 0.71, 15 quarters). Abnormal returns around Microsoft's announcements are confounded: Google announced Bard on February 6, 2023 and stumbled in its demonstration on February 8, and neither firm's abnormal return on the ads-in-chat announcement (March 29) was significant (Alphabet −1.5%, t = −1.01; Microsoft +0.1%, t = 0.06).

**Caveats.** StatCounter measures shares of page views referred by search engines on sites carrying its tracking code, not searches. Bing's share also depends on Windows and Edge defaults, which Microsoft changed over the same period, notably when it rebranded Bing Chat as Copilot in late 2023. A segmented trend with three breaks fits a single firm's history and cannot exclude other explanations. The Bing evidence is therefore consistent with Proposition 8 but is not a causal test, and the cross-firm test below does not support its broader prediction.

**Cross-firm test.** Bing is one case. Proposition 8 makes a cross-sectional prediction: the larger a search engine's legacy business, the later it should move to full AI answers, and the more likely it is to add summaries first. We coded the first public launch of each format for 17 search engines from company announcements and trade press, and measured legacy strength by each engine's average 2022 share of its home market (StatCounter, all devices). Timing is measured in months from ChatGPT's release (December 2022); Daum, which had not launched full answers by October 2026, is coded at 46 months.

Table 10. AI search formats by search engine, ordered by legacy market share.

| Search engine | Home market | 2022 share (%) | Summary above links (H) | Full AI answer (A) | Order |
| --- | --- | --- | --- | --- | --- |
| [Google](https://blog.google/products/search/google-search-ai-mode-update/) | U.S. | 87.2 | May 2024 | May 2025 | H then A |
| [Baidu](https://cn.chinadaily.com.cn/a/202309/01/WS64f1a3dea310936092f1fe2a.html) | China | 72.1 | By Aug. 2023 | Aug. 2023 (AI Partner) | Same month |
| [Yandex](https://yandex.com/company/news/16-04-2024) | Russia | 49.2 | Feb. 2024 | Apr. 2024 (Neuro) | H then A |
| [Naver](https://www.dailian.co.kr/news/view/1660449) | Korea | 24.0 | Mar. 2025 | June 2026 (AI Tab) | H then A |
| [Yahoo! JAPAN](https://www.lycorp.co.jp/ja/news/release/009460/) | Japan | 15.9 | Oct. 2024 | Oct. 2024 | Same day |
| [Seznam](https://www.lupa.cz/aktuality/seznam-rozsiril-testovani-seznam-asistenta-uzivatele-na-ai-chatbota-narazi-i-ve-vyhledavani/) | Czechia | 12.2 | Jan. 2025 | May 2026 | H then A |
| [Sogou](https://www.woshipm.com/share/6484203.html) | China | 7.6 | Oct. 2026 | Oct. 2026 | Same month |
| [Bing](https://autos.yahoo.com/microsoft-reveals-how-its-putting-ads-in-bings-ai-chatbot-052014029.html) | U.S. | 6.9 | — | Feb. 2023 | A first |
| [360 Search](https://m.thepaper.cn/newsDetail_forward_26181929) | China | 3.4 | Sept. 2023 (placement unclear) | Jan. 2024 | H then A |
| [Yahoo](https://unified.www.yahooinc.com/press/introducing-yahoo-scout-a-new-ai-answer-engine) | U.S. | 3.1 | Not found | Jan. 2026 (beta) | A only |
| [DuckDuckGo](https://spreadprivacy.com/ai-chat/) | U.S. | 2.4 | Mar. 2023 | June 2024 | H then A |
| [Daum](https://news.mtn.co.kr/news-detail/2026070108501174402) | Korea | 1.6 | July 2026 (beta) | Not launched | H only |
| [Ecosia](https://onlinemarketing.de/technologie/ki-suche-mit-nachhaltigkeit-ecosia-setzt-auf-ai-overviews) | Germany | 1.0 | Dec. 2025 | Dec. 2025 (beta) | Same day |
| [Qwant](https://www.mac4ever.com/web/194375-qwant-lance-son-ia-de-quoi-se-passer-de-google-en-europe) | France | 0.8 | Not found | Jan. 2026 | A only |
| [Brave](https://brave.com/blog/brave-search-chat-mode/) | Global | <0.1 | Mar. 2023 | Nov. 2024 | H then A |
| [Perplexity](https://www.ivp.com/content/perplexity-where-knowledge-begins/) | AI-native | 0 | — | Dec. 2022 | A only |
| [You.com](https://voicebot.ai/2022/12/28/new-youchat-chatbot-offers-chatgpt-style-generative-ai-search-engine/) | AI-native | 0 | — | Dec. 2022 | A only |

Table 11. Rank correlation between 2022 legacy share and months until full AI answers (positive = larger firms later, as predicted).

| Sample | N | Spearman ρ | p |
| --- | --- | --- | --- |
| All search engines | 17 | +0.17 | 0.51 |
| Excluding AI-natives | 15 | −0.21 | 0.46 |
| Excluding AI-natives and China | 12 | −0.16 | 0.62 |
| Engines with in-house frontier models (Google, Baidu, Yandex, Naver, Seznam, Bing, 360) | 7 | +0.21 | 0.65 |
| Same, coding Baidu's full answer at its July 2025 search overhaul | 7 | +0.39 | 0.38 |
| Engines without in-house models | 10 | +0.50 | 0.14 |

**Results.** The cross-firm prediction is not supported. Legacy share and the timing of full answers are not significantly related in any sample, and the sign depends on whether AI-native services are included. Two patterns stand out. First, the summary step is common among large engines: three of the four engines with more than 20% home share (Google, Yandex, Naver) added summaries before full answers, against four of nine engines below 5%. Second, the smallest legacy engines were not early. Seznam, Sogou, Daum, Qwant, Ecosia, and Yahoo all reached full answers late or not at all, even though they had little to lose.

**Interpretation and a test of Proposition 9.** Proposition 8 treats the ability to offer full answers as given. The small engines' delays suggest that scale and capability also govern timing, which Proposition 9 formalizes: adoption should be fastest at intermediate shares and faster for engines with in-house models. We regress months until full answers on legacy share, its square, and an indicator for an in-house frontier model, excluding the two AI-native entrants (N = 15; heteroskedasticity-robust standard errors).

Table 12. Months until full AI answers, 15 legacy search engines.

| Specification | Share | Share squared | In-house model | R² |
| --- | --- | --- | --- | --- |
| (1) In-house model only |  |  | −11.6 (p = 0.11) | 0.18 |
| (2) Share and share squared | −29.2 (p = 0.52) | +19.0 (p = 0.73) |  | 0.08 |
| (3) All three | +11.7 (p = 0.85) | −15.6 (p = 0.82) | −11.8 (p = 0.31) | 0.18 |
| (4) As (3), Baidu coded at its July 2025 search overhaul | +31.4 (p = 0.63) | −24.8 (p = 0.72) | −12.9 (p = 0.27) |  |
| (5) As (3), excluding China (N = 12) | −7.8 (p = 0.93) | +9.5 (p = 0.90) | −4.8 (p = 0.80) |  |

Engines with in-house frontier models reached full answers about 12 months earlier on average (21.6 vs. 33.1 months), in line with part (ii), but the difference is not statistically significant. The data show no inverted-U relation with share: the share terms are small relative to their standard errors and change sign across specifications. The cross-firm evidence therefore neither confirms nor rejects Proposition 9; with 15 engines, month-level dates, and share as a proxy for scale and legacy profit, it cannot separate the two forces. A sharper test would use engine-level search revenue and model-licensing contracts, or the timing of features within a firm across markets of different size. China's engines add a further constraint: Baidu and 360 released their public products in the same period that regulators first approved generative AI services.

**Legacy revenue instead of share.** Market share measures position, not what an engine stands to lose. We therefore collected each engine's 2022 search advertising revenue, or the closest reported line, from annual reports and filings, converted at 2022 average exchange rates ([IRS](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates)).

Table 13. Legacy search advertising revenue, 2022, and months until full AI answers.

| Search engine | Reported line | Revenue (US$ millions) | Months until full answers |
| --- | --- | --- | --- |
| Google | Google Search & other, sum of 2022 quarters from [Alphabet's earnings releases](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001652044&type=8-K) | 162,450 | 29 |
| Bing | [Microsoft search and news advertising](https://www.sec.gov/Archives/edgar/data/789019/000095017023035122/msft-20230630.htm), calendar 2022, gross of TAC | 12,022 | 2 |
| Baidu | [Baidu Core online marketing services](https://www.sec.gov/Archives/edgar/data/1329099/000119312523076192/d362351d20f.htm), includes feed ads | 10,330 | 8 |
| Yandex | [Search and Portal segment](https://www.sec.gov/Archives/edgar/data/1513845/000155837023006319/yndx-20221231x20f.htm), includes portal and ad network | 3,214 | 16 |
| Naver | [Search Platform segment](https://www.navercorp.com/navercorp_/ir/earningsRelease/2023/4Q22%20Naver_Earnings_Eng.pdf), includes display | 2,762 | 42 |
| Yahoo! JAPAN | [Search ads](https://static.seekingalpha.com/uploads/sa_presentations/979/92979/original.pdf), fiscal year to March 2023 | 1,481 | 22 |
| Sogou | [Search and search-related revenue](https://www.sec.gov/Archives/edgar/data/1713947/000110465921038046/sogo-20201231x20f.htm), 2020 (last reported) | 837 | 46 |
| 360 Search | [Internet advertising and services](https://paper.cnstock.com/html/2023-04/22/content_1752803.htm), all ads | 700 | 13 |
| Daum | [Kakao Portal Biz](https://www.kakaocorp.com/page/detail/10897?lang=ENG), sum of quarters | 328 | 46 (not launched) |
| Seznam | [Total revenue](https://blog.seznam.cz/en/2023/05/company-seznam-cz-reports-the-revenues-of-czk-5-928-billion-for-the-year-2022/) | 254 | 41 |
| DuckDuckGo | [Company statement, “more than $100 million”](https://www.wkrg.com/news/business/ap-duckduckgo-founder-says-googles-phone-and-manufacturing-partnerships-thwart-competition/amp/) | 100 | 18 |
| Ecosia | [Total income, monthly reports](https://blog.ecosia.org/ecosia-financial-reports-tree-planting-receipts/) | 36 | 36 |
| Brave | [Analyst estimate of total revenue](https://sacra.com/c/brave/) | 20 | 23 |

The revenue lines are not like-for-like: several are gross of traffic acquisition costs or include non-search advertising, and the smallest are estimates. Revenue for Qwant and Yahoo (U.S.) was not available.

With revenue in place of share, the relation runs, if anything, against the cannibalization prediction. Engines with more legacy revenue reached full answers somewhat earlier (Spearman ρ = −0.35, p = 0.24, N = 13; ρ = −0.25, p = 0.49 excluding China). In regressions on log revenue, its square, and the in-house model indicator, no coefficient is close to significant (all p > 0.45). The ordering at the top is the most informative. Bing, with the second-largest legacy revenue in the sample ($12.0 billion, gross of traffic acquisition costs), moved first; Baidu and Yandex followed within 16 months; Google, the largest, took 29 months; and Naver took 42. Bing was therefore not a firm with little to lose in absolute terms, only relative to Google, and its early move is better explained by its privileged access to OpenAI's models and by Microsoft's other gains from AI (cloud and Windows) than by a small legacy business. Across the available evidence, scale and capability appear to govern timing more than the size of the legacy business, which supports the fixed-cost channel of Proposition 9 and offers no support for the cannibalization channel of Propositions 8 and 9 in cross-firm data.

**Within-firm test: Google across countries.** Cross-firm comparisons confound legacy profit with capability. Holding the firm fixed removes that confound: Google's capability is the same everywhere, while the value of its legacy search business, the size of its markets, and regulation differ across countries. We dated the first month in which AI Overviews and AI Mode were available in each of 49 countries, from Google's announcements and archived copies of Google's help pages that list supported countries and languages ([AI Overviews](https://support.google.com/websearch/answer/14901683), [AI Mode](https://support.google.com/websearch/answer/16011537)). AI Mode reached the United States in May 2025 ([Google 2025b](https://blog.google/products/search/google-search-ai-mode-update/)), India and the United Kingdom in July, about 180 more countries in English in August ([Google 2025c](https://blog.google/products/search/ai-mode-agentic-personalized/)), local languages from September, the EU/EEA, Switzerland, and Australia in October ([Google 2025d](https://blog.google/products/search/ai-mode-expands-languages-locations/)), Türkiye in February 2026, and France in July 2026. We regress months until availability on log GDP per capita, a proxy for the value of a query to advertisers and hence for legacy profit per query; log internet users, a proxy for scale; and indicators for the EU/EEA, English-speaking markets, and the two markets held back by regulatory disputes (France and Türkiye). Covariates are from the [World Bank](https://data.worldbank.org/); Taiwan and Pakistan lack data, leaving N = 47.

Table 14. Months until Google AI Mode by country (N = 47; heteroskedasticity-robust p-values in parentheses).

| Variable | AI Mode, any language | AI Mode, local language | AI Mode, any language, outside EU and regulated markets (N = 30) | Months from AI Overviews to AI Mode |
| --- | --- | --- | --- | --- |
| Log GDP per capita | −0.07 (0.67) | −1.15 (<0.01) | −0.18 (0.29) | +0.09 (0.79) |
| Log internet users | −0.26 (0.10) | −0.72 (<0.01) | −0.34 (0.04) | +1.12 (<0.01) |
| EU/EEA | +1.92 (<0.01) | +1.33 (<0.01) |  | −0.91 (0.26) |
| English-speaking | −0.25 (0.35) | +0.67 (0.30) | −0.19 (0.47) | +2.25 (<0.01) |
| France and Türkiye | +7.68 (<0.01) | +7.36 (<0.01) |  | −8.18 (<0.01) |
| R² | 0.90 | 0.64 |  | 0.59 |

**Results.** Three findings stand out. First, regulation dominates: the EU/EEA received AI Mode about two months later than comparable markets, and France and Türkiye seven to eight months later still. Second, scale speeds adoption: larger markets received AI Mode earlier, in any language outside the EU (p = 0.04) and in the local language (p < 0.01), as the fixed-cost channel of Proposition 9 predicts. Third, there is no sign of a cannibalization delay. Markets where a query is worth more to advertisers did not receive full answers later; in their local languages they received them earlier (p < 0.01). Larger and English-speaking markets kept summaries longer before full answers arrived, but this reflects their early access to AI Overviews rather than a later switch.

**Interpretation.** GDP per capita raises both the legacy profit per query R and the ad productivity of AI answers m, so it acts mainly as a measure of market value, which favors early entry when entry has a fixed cost per market (for example, localization). The prediction of Proposition 8 depends on the ratio of m to R, which income alone cannot isolate. The within-firm evidence therefore supports the fixed-cost and scale channel and is inconsistent with a cannibalization delay large enough to show up in Google's rollout across countries. Rollouts in waves leave little independent variation, so these estimates describe Google's sequencing rather than causal effects.

### 5.7 A Trust Shock: The AI Overviews Errors of May 2024

Section 4.8 separates two reasons why users stop clicking: trust in AI answers and the effort that reading results requires. The widely publicized AI Overviews errors of late May 2024 lowered trust without changing that effort, so they allow a test. If trust drives clicking, clicks out of search should rise after the errors (Proposition 10(iv)); if effort drives it, clicks should change little. We use daily pageviews of English Wikipedia, the edition most exposed to AI Overviews in the United States, then the only market with AI Overviews. We compare English with the ten other largest editions in a triple difference: English minus other editions, 2024 minus the same weekdays of 2023, by period relative to the four weeks before the launch on May 14 (Table 15). Inference uses Newey–West standard errors on the daily series and a placebo comparison in which each other large edition is treated in turn. Figure 5 plots the daily gap.

&#91;embedded content: Wikimedia hourly projectviews dumps, four sampled U.S.-daytime hours per day, April–July 2023 and 2024; 2023 dates shifted 364 days to align weekdays and Memorial Day\]

Table 15. Change in English Wikipedia views relative to large editions, year over year, by period (versus April 15–May 13, 2024).

| Period | Desktop | Mobile web | All |
| --- | --- | --- | --- |
| AI Overviews live (May 14–22) | −0.8% (p = 0.74) | −0.7% (p = 0.71) | −0.4% (p = 0.78) |
| Errors go viral (May 23–31) | −3.4% (p = 0.15) | −1.6% (p = 0.31) | −1.8% (p = 0.07) |
| June 2024 | −4.9% (p < 0.01) | −2.5% (p = 0.12) | −3.3% (p < 0.01) |
| July 2024 | −3.9% (p = 0.03) | −3.0% (p = 0.02) | −3.6% (p < 0.01) |
| Placebo p-value, June | 0.40 | 0.70 | 0.60 |

Clicks out of search did not rise after the trust shock. English Wikipedia views did not change in the week after AI Overviews launched, and after the errors went viral they fell further relative to other editions, by about 4% through June and July. This happened even though Google cut back AI Overviews at the same time, from about 11% to 7% of queries by the end of June ([Search Engine Land 2024](https://searchengineland.com/google-ai-overviews-visibility-new-low-444048)), which on its own should have raised clicks. The result is the opposite of what the trust account predicts and is consistent with effort as the main driver. The evidence is weak in two respects. The June and July declines are significant in the daily time series but not relative to the variation among other large editions (placebo p = 0.40 to 0.70), and English Wikipedia is an imperfect measure of U.S. clicks, since much of its traffic comes from outside the United States. With these caveats, the trust shock moved clicks in the wrong direction for the trust account, which supports the view that the convenience of AI answers, more than trust in them, keeps users from reading search results.

### 5.8 Summary of Evidence and Remaining Tests

Table 16. Model predictions and empirical support.

| Prediction | Source | Evidence | Verdict |
| --- | --- | --- | --- |
| Premise: more AI use, fewer searches | Model setup (s rises) | Individual chatbot adopters search more than 20% less (Padilla et al. 2026), but no dose-response across U.S. states or European countries, and Google queries still growing (Tables 3–4) | Mixed: supported for individual adopters, not in aggregate |
| Narrow premise: AI reduces clicks after a search | Model setup | Click-through 8% vs. 15% with AI summaries; Stack Overflow −25%; desktop Wikipedia views −9% after AI Overviews launch, marginal (Table 4, Figure 1) | Supported |
| Effort, more than trust, drives the fall in clicks | Section 4.8; Prop. 10 | Skeptical users rarely check sources; click effects concentrated in informational queries; English Wikipedia views did not rise after the May 2024 trust shock (Table 15, Figure 5) | Consistent; placebo p = 0.40–0.70 |
| Signals of AI substitution reduce the value of search-dependent firms, not ad firms in general | Prop. 4 | Alphabet CAR −7.0% and −12.6% on displacement news; Meta flat; pooled Z = −4.32 (Table 5) | Supported |
| Introducing ads into own AI answers raises incumbent value | Props. 1–2 | +6.0% for AI Mode ads (2025); no reaction for AI Overviews ads (2024); pooled Z = 0.88 (Table 5) | Partly supported |
| A rival's ads raise incumbent value (base model, η = 0) | Prop. 3 | No significant reaction to the announcement or launch of ChatGPT ads (Table 5) | Not supported |
| A rival's ads have little net effect on a dominant incumbent when εw\_I ≈ 1 | Prop. 6 | Null event-study result together with ε ≈ 1 (Tables 5 and 8) | Consistent |
| Ad price rises when inventory grows more slowly (scarcity dividend) | Prop. 7 | CPC growth falls one-for-one with click growth, 2023–2026 (Table 8, Figure 3) | Supported, not causal |
| Search revenue falls behind the ad cycle as AI diffuses | Prop. 4 | Slower growth since 2023 relative to Meta, but placebo breaks fit equally well (Tables 6–7, Figure 2) | Inconclusive |
| Ad load rises with inference cost | Props. 2, 5 | Requires answer-level data | Untested |
| An incumbent adds summaries before full answers; a firm with relatively little legacy profit goes straight to full answers | Prop. 8 | Google: AI Overviews (2024) before AI Mode (2025); Bing: full answers in Feb. 2023; Bing's share gains stalled after Google's summaries (Table 9, Figure 4) | Consistent, not causal |
| Engines and markets with more legacy profit adopt full answers later | Props. 8–9 | No relation with legacy share or revenue across 15–17 engines (Tables 10–13); within Google, higher-value markets were not delayed (Table 14) | Not supported |
| Capability and scale speed adoption | Prop. 9 | In-house models about 12 months earlier (p = 0.11); larger markets earlier within Google (Table 14); no inverted-U in share (Table 12) | Partly supported |
| Regulation delays deployment | Fixed cost K in Prop. 9 | EU/EEA about 2 months later; France and Türkiye 7–8 months later still (Table 14) | Supported |

**Why Proposition 3 fails, and what replaces it.** The base model lets a rival's ads affect the incumbent only through consumers. The extension in Section 4.5 adds the advertiser side: the rival's ads also expand ad inventory and lower the price of the incumbent's ads. Proposition 6 shows that the net effect is positive only if εw\_I < 1. The estimate in Table 8 implies ε close to 1, and Google holds most search ad inventory, so the two effects roughly cancel. This matches the null result. Anticipation, since media reported OpenAI's ad plans before January 2026, and the small scale of the initial pilot may also have contributed.

**Remaining tests.** Three designs could identify the AI effect more cleanly than firm-level time series:

1. *Staggered rollout.* AI Overviews and AI Mode launched in different countries at different dates. A difference-in-differences design using country-level search ad spend (for example, from advertiser panels) would identify the effect of AI answers on search monetization.
2. *Query categories.* Commercial categories with high legacy profit R (travel, finance, retail) should lose more revenue when AI answers appear than informational categories, unless AI ad productivity is correspondingly higher (Proposition 4).
3. *Answer-level ad load.* A panel of AI answers, coding sponsored content per answer across platforms and model generations, would test whether ad load tracks inference cost (Proposition 2).

Replication files (price data, scraped SEC revenue series, and estimation code) are available from the authors.

## 6. Discussion

### 6.1 Managerial Implications

For incumbent search platforms, the model suggests that the relevant question is not whether to place advertising in AI answers but how to clear the recovery threshold in Proposition 4. Investments that make ads more productive in a conversational setting, such as formats that draw on intent expressed over several turns or attribution that links an answer to a later purchase, are of first-order importance. Investments that lower inference cost are a different matter. In a competitive equilibrium they do not raise profit; their benefit is passed on to users in the form of lighter ad loads. They are worth making, but managers should not expect them to show up in margins.

For AI-native entrants, Proposition 3 implies that staying ad-free is an expensive and temporary way to stand apart. It helps to win users while outside capital lasts, but its cost rises with every additional answer served. The evidence in Section 5.6 adds a second lesson for all firms: the timing of an AI rollout appears to be set less by what a firm stands to lose than by whether it has its own model and how large its market is. A firm that waits for its legacy business to shrink before launching answers may find that rivals did not wait.

For advertisers, a conversation reveals more about intent than a keyword does, which should make targeting more precise. At the same time, our finding that users stop clicking because reading results takes effort, and not because they have come to trust AI more, implies that clicks will remain scarce even if AI answers are sometimes wrong. As clicks become rarer, pricing that rests on outcomes rather than clicks is likely to become more attractive to both sides.

### 6.2 Policy Implications

Advertising inside generated answers raises concerns that a separate column of sponsored links does not. If commercial content shapes the substance of an answer, users may not be able to tell advice from advertising. Disclosure rules that keep ads visibly apart from the answer raise the effective nuisance γ in the short run, but by protecting trust they may preserve differentiation t in the long run. Proposition 4 implies that such rules also raise the recovery threshold, an effect on incumbents that regulators should weigh against the gain in consumer protection. The trust model in Section 4.8 adds a further consideration. If users rarely verify AI answers, they cannot discipline a platform that blends ads into them, so rules on disclosure matter more, not less, when users are complacent.

Regulation already shapes how fast AI answers reach users. Section 5.6 shows that Google's AI features arrived about two months later in the European Union and seven to eight months later in France and Türkiye than in comparable markets. Whatever their merits, these delays redistribute the timing of the transition across countries, and they should be counted among its costs and benefits. Antitrust analysis may also need to adapt: if competition moves from the search box to the AI answer, market definitions built around general search services may soon be out of date.

### 6.3 Limitations and Future Research

The model is deliberately stylized, and several of its simplifications deserve mention. First, the core model is static. Sections 4.7 and 4.8 add a deployment date and a learning process for trust, but they do not let today's ad load erode tomorrow's demand; a fully dynamic model in which it does would probably yield lower equilibrium ad intensity. Second, we set subscriptions aside. A menu combining a free tier with ads and a paid tier without them (Prasad et al. 2003) would weakly dominate either pure model, and both incumbents and entrants already offer such menus. Third, the share of AI-amenable queries s is exogenous. Section 4.6 lets the incumbent choose how to serve those queries, but not how quickly users come to prefer answers. Fourth, the advertiser side in Section 4.5 is reduced-form, with a downward-sloping demand for exposure and price-taking platforms. A richer model would let advertisers choose where to advertise and let a dominant platform internalize its effect on the price of ads. We also leave out the publishers whose content is used to train and ground the models, although their incentives to keep producing that content may ultimately limit how good AI answers can be.

The empirical analysis has limitations of its own. The monetization tests rely on a single incumbent, a small number of events, and a benchmark firm (Meta) that faces its own shocks. The cross-firm and cross-country analyses of timing have between 17 and 47 observations, so they can detect only large effects; the capability result (p = 0.11) in particular should be read as suggestive. Our measures of clicks come from Wikipedia, which is one destination among many. The trust-shock test exploits a single episode of public errors, and a null result there cannot rule out that trust matters in other settings or over longer horizons. Nor can aggregate traffic data observe effort directly; a controlled experiment that varies the cost of reading results while holding answer accuracy fixed would provide a sharper test. Finally, several of the sources we use to date product launches are trade-press reports rather than company documents. The research designs listed in Section 5.8 would address many of these limitations with data we could not obtain.

## 7. Conclusion

Taken together, our results suggest that generative AI has not, in the aggregate, made people search less; it has made them click less. Individual chatbot adopters do run fewer searches (Padilla et al. 2026), but we find no sign that AI adoption reduced search activity across U.S. states or European countries. The staggered launch of AI Overviews, by contrast, points to fewer clicks out of search. Because sponsored search is sold by the click, the threat is to revenue per search rather than to search itself.

The model explains why advertising inside AI answers is close to unavoidable, since every answer costs money to produce, and it shows how that cost is divided between users and advertisers. One of its predictions fails: incumbents with more to lose do not wait longer to launch full answers. Across search engines and across Google's own markets, the pace is set by capability, market size, and regulation. Nor does trust seem to be the main reason users stop clicking. When AI Overviews made widely reported errors in May 2024, clicks did not recover, which is more consistent with users avoiding the effort of reading results than with users who trust AI and then learn not to.

The October 2026 repricing of Alphabet fits a market coming to terms with answers that are being deployed quickly while their monetization lags behind. Whether search platforms decline or reinvent themselves will depend less on whether people keep searching than on whether answers can carry advertising without losing the convenience, and the trust, that make them worth using.

## Statements

**Use of generative AI.** \[Author to complete before submission, following the INFORMS policy on AI tools: describe which tools were used, for which tasks (e.g., literature search, data collection code, drafting and editing), and confirm that the author reviewed and takes full responsibility for all content.\]

**Data and code availability.** All data used in this paper are publicly available: Wikimedia projectviews dumps, Google Trends, Eurostat (isoc\_ai\_iaiu, isoc\_ci\_ifp\_fu), World Bank World Development Indicators, StatCounter Global Stats, and company filings on SEC EDGAR. Code and processed data will be deposited in a public repository upon acceptance. \[Add repository link.\]

**Funding and conflicts of interest.** \[Author to complete.\]

## References

- Agarwal A, Hosanagar K, Smith MD (2011) Location, location, location: An analysis of profitability of position in online advertising markets. *J. Marketing Res.* 48(6):1057–1073.
- Agarwal S, Sen A (2026) [Randomized field experiment on Google AI Overviews and outbound clicks](https://ppc.land/ai-overviews-cut-publisher-clicks-39-8-in-first-randomized-study/). Working paper, SSRN (as reported by PPC Land).
- Aggarwal P, Murahari V, Rajpurohit T, Kalyan A, Narasimhan K, Deshpande A (2024) [GEO: Generative engine optimization](https://arxiv.org/abs/2311.09735v3). *Proc. 30th ACM SIGKDD Conf. Knowledge Discovery Data Mining*, 5–16.
- Alphabet Inc. (2026a) [Alphabet announces third quarter 2026 results](https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000080/googexhibit991q32026.htm). Form 8-K, Exhibit 99.1.
- Alphabet Inc. (2026b) [Alphabet announces second quarter 2026 results](https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000066/googexhibit991q22026.htm). Form 8-K, Exhibit 99.1.
- Alphabet Inc. (2026c) [Alphabet announces first quarter 2026 results](https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000043/googexhibit991q12026.htm). Form 8-K, Exhibit 99.1.
- Anderson SP, Coate S (2005) Market provision of broadcasting: A welfare analysis. *Rev. Econom. Stud.* 72(4):947–972.
- Android Authority (2024) [Report on the August 2024 expansion of Google AI Overviews](https://androidauthority.com/google-ai-overviews-expansion-3494705). August.
- Armstrong M (2006) Competition in two-sided markets. *RAND J. Econom.* 37(3):668–691.
- Balseiro S, Bhawalkar K, Deng Y, Feng Z, Mao J, Mehta A, Mirrokni V, Paes Leme R, Wang D, Zuo S (2025) [Position auctions in AI-generated content](https://arxiv.org/abs/2506.03309). Working paper, arXiv:2506.03309.
- Bloomberg (2026) [OpenAI to test targeted ads in ChatGPT, stepping up revenue push](https://www.bloomberg.com/news/articles/2026-01-16/openai-to-test-targeted-ads-in-chatgpt-stepping-up-revenue-push). January 16.
- Burtch G, Lee D, Chen Z (2024) [The consequences of generative AI for online knowledge communities](https://pmc.ncbi.nlm.nih.gov/articles/PMC11074245/). *Sci. Rep.* 14. doi:10.1038/s41598-024-61221-0.
- Callaway B, Sant'Anna PHC (2021) Difference-in-differences with multiple time periods. *J. Econometrics* 225(2):200–230.
- Casadesus-Masanell R, Zhu F (2010) Strategies to fight ad-sponsored rivals. *Management Sci.* 56(9):1484–1499.
- Chapekis A (2025) [Google users are less likely to click on links when an AI summary appears in the results](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/). Pew Research Center, July 22.
- Christensen CM (1997) *The Innovator's Dilemma* (Harvard Business School Press, Boston).
- del Rio-Chanona RM, Laurentsyeva N, Wachs J (2024) [Large language models reduce public knowledge sharing on online Q&A platforms](https://kti.krtk.hu/en/publikacio/r-maria-del-rio-chanona-nadzeya-laurentsyeva-johannes-wachss-article-in-the-pnas-nexus-2024/). *PNAS Nexus* 3(9):pgae400.
- Dubey KA, Feng Z, Kidambi R, Mehta A, Wang D (2024) [Auctions with LLM summaries](https://arxiv.org/abs/2404.08126). Working paper, arXiv:2404.08126.
- Duetting P, Mirrokni V, Paes Leme R, Xu H, Zuo S (2024) [Mechanism design for large language models](https://arxiv.org/pdf/2310.10826). *Proc. ACM Web Conf. 2024*, 144–155.
- Edelman B, Ostrovsky M, Schwarz M (2007) Internet advertising and the generalized second-price auction. *Amer. Econom. Rev.* 97(1):242–259.
- Engadget (2023) [Microsoft reveals how it's putting ads in Bing's AI chatbot](https://autos.yahoo.com/microsoft-reveals-how-its-putting-ads-in-bings-ai-chatbot-052014029.html). March 29.
- Engadget (2024) [Google is putting more restrictions on AI Overviews after it told people to put glue on pizza](https://www.engadget.com/google-is-putting-more-restrictions-on-ai-overviews-after-it-told-people-to-put-glue-on-pizza-011316780.html). May 31.
- Eurostat (2026) [64% of 16-24-year-olds used AI in 2025](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/edn-20260210-1). Datasets isoc\_ai\_iaiu (use of generative AI tools by individuals, 2025) and isoc\_ci\_ifp\_fu (frequency of internet use).
- Exploding Topics (2025) [AI trust gap research](https://explodingtopics.com/blog/ai-trust-gap-research). Survey report.
- Feizi S, Hajiaghayi M, Rezaei K, Shin S (2023) [Online advertisements with LLMs: Opportunities and challenges](http://www.sigecom.org/exchanges/volume_22/2/FEIZI.pdf). *ACM SIGecom Exchanges* 22(2).
- Fortune (2025) [Apple's Eddy Cue testimony on Safari search volume](https://fortune.com/2025/05/08/apple-eddy-cue-testimony-google-alphabet-safari-ai-search-features). May 8.
- Ghose A, Yang S (2009) An empirical analysis of search engine advertising: Sponsored search in electronic markets. *Management Sci.* 55(10):1605–1622.
- Google (2024a) [AI Overviews in Search: Launch and expansion updates](https://blog.google/products/search/ai-overviews-search-october-2024/). The Keyword (Google blog).
- Google (2025a) [AI Overviews expansion, May 2025 update](https://blog.google/products/search/ai-overview-expansion-may-2025-update/). The Keyword (Google blog), May 20.
- Google (2025b) [AI Mode in Google Search: U.S. launch update](https://blog.google/products/search/google-search-ai-mode-update/). The Keyword (Google blog), May.
- Google (2025c) [AI Mode: Agentic and personalized features and English expansion](https://blog.google/products/search/ai-mode-agentic-personalized/). The Keyword (Google blog), August.
- Google (2025d) [AI Mode expands to more languages and locations](https://blog.google/products/search/ai-mode-expands-languages-locations/). The Keyword (Google blog), October.
- Google (2025e) [Google Marketing Live 2025](https://blog.google/products/ads-commerce/google-marketing-live-2025/). The Keyword (Google blog), May 21.
- Google Search Help (2026) Supported countries and languages for [AI Overviews](https://support.google.com/websearch/answer/14901683) and [AI Mode](https://support.google.com/websearch/answer/16011537). Archived copies, 2024–2026.
- Grossman R, Liu S, Chen MK, Smith M, Borcea C, Chen Y (2026) [How generative AI disrupts search: An empirical study of Google Search, Gemini, and AI Overviews](https://arxiv.org/abs/2604.27790). *Proc. ACM SIGIR 2026*.
- Hajiaghayi M, Lahaie S, Rezaei K, Shin S (2024) [Ad auctions for LLMs via retrieval augmented generation](https://arxiv.org/abs/2406.09459). Working paper, arXiv:2406.09459.
- Hotelling H (1929) Stability in competition. *Econom. J.* 39(153):41–57.
- Internal Revenue Service (2026) [Yearly average currency exchange rates](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates). Accessed October 2026.
- Kaiser M, Schulze C (2026) [Frontiers: ChatGPT referrals to e-commerce websites: How do LLMs compare against traditional channels?](https://pubsonline.informs.org/doi/10.1287/mksc.2025.0489) *Marketing Sci.*, forthcoming.
- Khosravi M, Yoganarasimhan H (2026) [Impact of AI search summaries on website traffic: Evidence from Google AI Overviews and Wikipedia](https://arxiv.org/abs/2602.18455). Working paper, arXiv:2602.18455.
- Lyu L, et al. (2025) [Wikipedia contributions in the wake of ChatGPT](https://arxiv.org/abs/2503.00757). *Companion Proc. ACM Web Conf. 2025*.
- MacKinlay AC (1997) Event studies in economics and finance. *J. Econom. Literature* 35(1):13–39.
- MarketBeat (2026) [Alphabet Q3 earnings call highlights](https://www.marketbeat.com/instant-alerts/transcript-alphabet-q3-earnings-call-highlights-2026-10-29/). October 29.
- Melumad S, Yun JH (2025) [Experimental evidence of the effects of large language models versus web search on depth of learning](https://doi.org/10.1093/pnasnexus/pgaf316). *PNAS Nexus*.
- Microsoft Corp. (2026) [Quarterly report on Form 10-Q for the quarter ended March 31, 2026](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=10-Q). SEC EDGAR.
- Newey WK, West KD (1987) A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica* 55(3):703–708.
- Padilla N, Lam HT, Lambrecht A, Hollenbeck B (2026) [The impact of LLM adoption on online user behavior](https://www.msi.org/working-paper/the-impact-of-llm-adoption-on-online-user-behavior/). Working paper, Marketing Science Institute.
- Parker GG, Van Alstyne MW (2005) Two-sided network effects: A theory of information product design. *Management Sci.* 51(10):1494–1504.
- PPC Land (2025) [Google expands AI Overviews to more European markets](https://ppc.land/google-expands-ai-overviews-to-more-european-markets/). March.
- PPC Land (2026a) [ChatGPT targets Google's $224bn search ad business with $102bn bet](https://ppc.land/chatgpt-targets-googles-224bn-search-ad-business-with-102bn-bet/).
- PPC Land (2026b) [Google ends France AI Overviews blackout](https://ppc.land/google-ends-france-ai-overviews-blackout-as-68-users-flagged-the-gap/). July.
- Prasad A, Mahajan V, Bronnenberg B (2003) Advertising versus pay-per-view in electronic media. *Internat. J. Res. Marketing* 20(1):13–30.
- Reeves N, Yin W, Simperl E (2024) [Exploring the impact of ChatGPT on Wikipedia engagement](https://arxiv.org/abs/2405.10205). Working paper, arXiv:2405.10205.
- Rochet JC, Tirole J (2003) Platform competition in two-sided markets. *J. Eur. Econom. Assoc.* 1(4):990–1029.
- Search Engine Land (2024) [Google AI Overviews visibility falls to a new low](https://searchengineland.com/google-ai-overviews-visibility-new-low-444048). June.
- Simon FM, Nielsen RK, Fletcher R (2025) [Generative AI and news report 2025: How people think about AI's role in journalism and society](https://mediawell.ssrc.org/citations/generative-ai-and-news-report-2025-how-people-think-about-ais-role-in-journalism-and-society/). Reuters Institute for the Study of Journalism, University of Oxford.
- StatCounter (2026) [Search engine market share](https://gs.statcounter.com/search-engine-market-share). StatCounter Global Stats, January 2019–September 2026.
- TechCrunch (2025) [Wikipedia says traffic is falling due to AI search summaries and social video](https://techcrunch.com/2025/10/18/wikipedia-says-traffic-is-falling-due-to-ai-search-summaries-and-social-video). October 18.
- Varian HR (2007) Position auctions. *Internat. J. Indust. Organ.* 25(6):1163–1178.
- Wang et al. (2025) [Advertising or freemium: The revenue model decisions for competing artificial intelligence-based platforms](https://link.springer.com/chapter/10.1007/978-3-031-94184-9_2). *Proc. WHICEB 2025* (Springer).
- Wikimedia Foundation (2026) [Hourly projectviews dumps](https://dumps.wikimedia.org/other/pageviews/). Accessed October 2026.
- World Bank (2026) [World Development Indicators](https://data.worldbank.org/). Accessed October 2026.
- Xu RR, Feng YK, Chen H (2023) [ChatGPT vs. Google: A comparative study of search performance and user experience](https://papers.ssrn.com/abstract=4498671). Working paper, SSRN 4498671.
- Yahoo Finance (2026) [Alphabet loses $475 billion in market value, the biggest drop in its history](https://finance.yahoo.com/markets/article/alphabet-heads-for-a-500-billion-drop-in-market-value-the-biggest-in-its-history-134824763.html). October 29.
- Zhang L, Jiao C, Li B, Xiong C (2026) [An economic framework for generative engines: Advertising or subscription?](https://arxiv.org/abs/2603.29071) Working paper, arXiv:2603.29071.

## Appendix: Proofs

Let k ≡ γ/(2t), so x̂ = 1/2 + k(a\_E − a\_I). The AI profits are π\_I = s·x̂·(m\_I a\_I − c) and π\_E = s·(1 − x̂)·(m\_E a\_E − c).

**Proof of Proposition 1.** For the incumbent,

```latex
\frac{\partial \pi_I}{\partial a_I} = s\left[m_I \hat{x} - k\,(m_I a_I - c)\right], \qquad \frac{\partial^2 \pi_I}{\partial a_I^2} = -2 s k m_I < 0
```

At a\_I = 0, profit is −s·x̂·c < 0 and the derivative is s(m\_I x̂ + kc) > 0. A small increase in a\_I therefore strictly raises profit, so a\_I = 0 is not a best response. The argument for E is symmetric. ∎

**Proof of Proposition 2.** Strict concavity implies that best responses are given by the first-order conditions:

```latex
a_I = \frac{1}{4k} + \frac{a_E}{2} + \frac{c}{2m_I}, \qquad a_E = \frac{1}{4k} + \frac{a_I}{2} + \frac{c}{2m_E}
```

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
