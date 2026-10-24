# 결과 요약: Winter 외(2026) 대응 분석, Amazon Reviews 2023 (n≈25,800)

**상태: 탐색적 분석. 사전등록 없음. 2,000건 파일럿을 본 뒤 설계.** 원문 데이터와 LLM 응답은 저장소에 포함하지 않음(재현용 리뷰 ID 목록과 코드만 공개 예정).

## 설계
- 표본: Amazon Reviews 2023 4개 카테고리 × 6,500건(휴대폰·사무용품=탐색재, 뷰티·주방=경험재; 휴대폰·뷰티=쾌락, 사무용품·주방=실용. **카테고리 단위 분류는 우리의 가정**). 사용자당 최대 5건. 중복 review_id 제거 후 25,783건.
- 괴리 = |저자 별점 − LLM이 텍스트로 추정한 별점|. 프롬프트: "텍스트만 보고 저자의 별점(1–5)을 추정"(temperature 0).
- Study 2: helpful votes ~ 괴리 (× 경험재) + 글자 수 + 별점 더미 + 이미지 + 리뷰 나이. (a) Tobit(0에서 좌측 절단, 상품 단위 클러스터 SE) (b) NB2 + log(리뷰 나이) offset.
- LLM 3종: Claude Haiku 5.5, Llama 3.3 70B, GPT-4.1 nano (모두 OpenRouter 경유).

## 결과: 세 모델 비교
| 모델 | r(저자 별점, LLM 별점) | 정확 일치 | Tobit 괴리 | Tobit 괴리×경험재 | NB2 괴리 (Model 1, IRR) | NB2 괴리 (Model 2, IRR) | NB2 괴리×경험재 (IRR) |
|---|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | .907 | 70.7% | 1.28 (p=.026) | −0.59 (p=.40) | 1.26 (p=.001) | 1.25 (p=.021) | 1.02 (p=.88) |
| Llama 3.3 70B | .923 | 79.0% | 1.38 (p=.025) | −1.06 (p=.12) | 1.24 (p=.003) | 1.36 (p=.003) | 0.82 (p=.09) |
| GPT-4.1 nano | .889 | 64.6% | 1.45 (p=.007) | −1.05 (p=.13) | 1.22 (p=.001) | 1.29 (p=.006) | 0.90 (p=.38) |

논문(Tobit Model 2): 괴리 +4.345 (p=.014), 괴리×경험재 −7.239 (p<.001). 척도가 달라 계수 크기는 직접 비교 불가.

모델 간 괴리 변수의 상관: Claude–Llama .72, Claude–GPT .76, Llama–GPT .63.

## 읽는 법
1. **재현된 것**: LLM이 별점을 잘 맞힌다(r .89–.92). 괴리의 **양(+)의 효과**가 세 모델·두 모형에서 일관(IRR 1.22–1.36). 논문의 Model 2 탐색재 효과(+4.345)와 방향 일치.
2. **재현되지 않은 것**: 경험재에서 효과가 더 낮다는 상호작용. 모두 유의하지 않고, NB2에서는 부호가 모델에 따라 갈림(0.82–1.02).
3. **논문 초록의 핵심 주장("괴리가 클수록 유용성 낮음")은 우리 관찰 데이터에서 지지되지 않음**(오히려 양의 연관). 논문 Study 3의 실험(독자가 인지한 불일치 조작)에 대한 반박이 아니라, 관찰 연관이 다르다는 의미.
4. 괴리 변수 자체는 모델 의존성이 있으나(상관 .63–.76) 결론은 모델에 의존하지 않음 → 강건성 근거.
5. 한계: 쾌락재/실용재 분류가 카테고리 단위(Study 1에서 쾌락재 효과 재현 안 됨), 사전등록 없음, 클러스터·표본 설계 차이, Tobit의 정규 잠재변수 가정(반응 0 비율 약 80%).
6. **영과잉(ZINB) 점검 — 해결**: 처음 "수렴 실패"로 보였던 것은 버그가 아니라 **경계해**였다. 영과잉 성분(로짓: 상수 + 경험재)의 절편이 −∞로 발산해 구조적 0 확률이 10⁻⁹⁴~10⁻¹⁰² 수준이 되고, ZINB의 로그우도가 일반 NB2와 소수점까지 같다(Claude −22339.85 / Llama −22345.46 / GPT −22291.97). 헤시안이 특이해지는 것은 영과잉 모수가 식별되지 않기 때문이다. AIC는 NB2가 4 낮다(추가 모수 2개). 결론: **이 데이터의 0(약 79%)은 NB2 분포 자체로 설명되며 별도의 영과잉 성분은 필요 없다.** NB2를 주 모형으로 쓰는 것이 정당하다. (`tools/zinb_check.py`, `models.zero_inflation_check`)

## Update: original WZH prompt (six model–prompt combinations)
Original system prompt from the supplementary material (Web Appendix 7, GUIDE-LLM items C.1/C.2; see `prompts_orig/`), temperature 0.2, raw review text as user message; three sentences joined by spaces (separator unknown).

| Prompt | LLM | N | r | Exact | Tobit gap (M2) | Tobit gap×exp | NB2 gap IRR (M1) | NB2 gap IRR (M2) | NB2 gap×exp IRR |
|---|---|---|---|---|---|---|---|---|---|
| ours | Claude Haiku 5.5 | 25,783 | .907 | 70.7% | 1.28 (.026) | −0.59 (.40) | 1.26 (.001) | 1.25 (.021) | 1.02 (.88) |
| ours | Llama 3.3 70B | 25,783 | .923 | 79.0% | 1.38 (.025) | −1.06 (.12) | 1.24 (.003) | 1.36 (.003) | 0.82 (.09) |
| ours | GPT-4.1 nano | 25,751 | .889 | 64.6% | 1.45 (.007) | −1.05 (.13) | 1.22 (.001) | 1.29 (.006) | 0.90 (.38) |
| original | Claude Haiku 5.5 | 25,711 | .897 | 70.9% | 1.13 (.044) | −0.60 (.46) | 1.21 (.015) | 1.25 (.048) | 0.92 (.57) |
| original | Llama 3.3 70B | 25,783 | .921 | 78.3% | 1.34 (.026) | −1.01 (.16) | 1.28 (.001) | 1.36 (.002) | 0.89 (.34) |
| original | GPT-4.1 nano | 25,736 | .888 | 67.6% | 0.71 (.16) | −0.54 (.44) | 1.21 (.007) | 1.19 (.097) | 1.03 (.83) |

- Sign of the gap effect is positive in all six; the interaction is non-significant in all six.
- Significance of the gap effect varies: the GPT-4.1 nano / original-prompt combination loses significance in Tobit and is marginal in NB2 Model 2.
- Star-by-star gap profile: with our prompt the three-star gap is largest in all LLMs; with the original prompt the one-star gap is 0.17–0.54 and the three-star gap 0.53–0.67 (only GPT-4.1 nano has them equal). **Correction:** an earlier note that the original prompt "reproduces WZH's one-star pattern" was based on GPT-4.1 nano alone and overstated; it does not hold across LLMs.
- Hedonic coefficient on the gap (original prompt): −.006 (p=.49), −.002 (p=.79), −.005 (p=.61).
- Original paper's own GPT-5-nano check (Web Appendix 4): gap +6.29 (p=.001) for search goods, interaction −8.46 (p<.001); N=28,867 (15,509 censored), 383 product clusters.

## Update: product-level search/experience and hedonic/utilitarian labels (LLM-assigned)
Product metadata (title, categories, features) for all 20,672 sampled products was streamed from the Amazon 2023 meta files (`tools/fetch_amazon_meta.py`). Claude Haiku 5.5 labelled every product (`product_labels.py`; definitions after Nelson 1970 / WZH, anchors: smartphone = search & hedonic, printer = search & utilitarian, mascara = experience & hedonic, vacuum cleaner = experience & utilitarian). Llama 3.3 70B labelled a random 3,000 products for a cross-check.

**Agreement (2,999 products):** search/experience 88.8%, kappa .755; hedonic/utilitarian 87.6%, kappa .698; both dimensions 77.6%. Labels are **not human-validated**; agreement between two LLMs does not exclude shared errors, and misclassification attenuates interactions toward zero.

**Category assumption vs product-level labels (share, Claude):** Cell Phones experience 5.4% / hedonic 11.6% (assumed hedonic); Office 15.9% / 11.6%; Beauty 88.5% / 48.3%; Home & Kitchen 33.6% / 29.3% (assumed experience). Analysis sample: 25,781 reviews; experience 37.0%, hedonic 22.5%.

| Prompt | LLM | Labels | Tobit gap (p) | Tobit gap×exp (p) | NB2 gap IRR M1 (p) | NB2 gap IRR M2 (p) | NB2 gap×exp IRR [CI] (p) | Hedonic coef. on gap (p) |
|---|---|---|---|---|---|---|---|---|
| ours | Claude | category | 1.28 (.026) | −0.59 (.40) | 1.26 (.001) | 1.25 (.021) | 1.02 [0.79, 1.31] (.88) | −.010 (.25) |
| ours | Claude | **product** | 1.33 (.012) | −0.82 (.29) | 1.28 (<.001) | 1.30 (.001) | 0.95 [0.73, 1.22] (.67) | **−.029 (.001)** |
| ours | Llama | category | 1.38 (.025) | −1.06 (.12) | 1.24 (.003) | 1.36 (.003) | 0.82 [0.65, 1.03] (.09) | +.003 (.72) |
| ours | Llama | **product** | 1.03 (.054) | −0.51 (.44) | 1.25 (.002) | 1.35 (.001) | 0.80 [0.65, 1.00] (.049) | **−.017 (.031)** |
| ours | GPT-4.1 nano | category | 1.45 (.007) | −1.05 (.13) | 1.22 (.001) | 1.29 (.006) | 0.90 [0.72, 1.14] (.38) | −.004 (.66) |
| ours | GPT-4.1 nano | **product** | 1.11 (.016) | −0.49 (.47) | 1.23 (.001) | 1.29 (.001) | 0.88 [0.70, 1.11] (.30) | −.017 (.078) |
| orig | Claude | category | 1.13 (.044) | −0.60 (.46) | 1.21 (.015) | 1.25 (.048) | 0.92 [0.70, 1.22] (.58) | −.006 (.49) |
| orig | Claude | **product** | 1.05 (.031) | −0.61 (.49) | 1.23 (.005) | 1.31 (.002) | 0.83 [0.64, 1.07] (.15) | **−.026 (.004)** |
| orig | Llama | category | 1.34 (.026) | −1.01 (.17) | 1.28 (.001) | 1.36 (.002) | 0.89 [0.69, 1.14] (.34) | −.002 (.79) |
| orig | Llama | **product** | 1.03 (.053) | −0.46 (.52) | 1.29 (.001) | 1.36 (<.001) | 0.87 [0.68, 1.12] (.27) | **−.017 (.032)** |
| orig | GPT-4.1 nano | category | 0.71 (.16) | −0.54 (.44) | 1.21 (.007) | 1.19 (.097) | 1.03 [0.79, 1.34] (.83) | −.005 (.61) |
| orig | GPT-4.1 nano | **product** | 0.61 (.17) | −0.39 (.58) | 1.22 (.004) | 1.23 (.016) | 0.98 [0.76, 1.27] (.87) | **−.021 (.025)** |

**Reading:**
1. H3 (hedonic goods show smaller gaps): not supported with category coding, **supported in direction in all six combinations with product-level coding** (−.017 to −.029; five of six p < .05; WZH −.058). The category assumption (e.g., all Cell Phones hedonic) was the likely reason for the earlier null.
2. H2 (experience interaction): still not significant. NB2 interaction IRR is below 1 in all six product-level combinations (0.80–0.98; category: four of six), i.e. directionally as in WZH, but p-values are .049–.87 (one borderline value among six, uncorrected). Tobit interaction −0.39 to −0.82 (p .29–.58).
3. H1: the gap effect for search goods stays positive (NB2 M1 IRR 1.22–1.29, p ≤ .005). Point estimates imply a net gap effect for experience goods that is not negative (e.g., 1.30 × 0.95 ≈ 1.23 for Claude/our prompt; 1.35 × 0.80 ≈ 1.08 for Llama/our prompt; products of point estimates, not tested).
4. ZINB again collapses to NB2 (inspected for Claude/our prompt and Llama/original prompt).
5. Caveats: LLM labels (kappa .70–.76) contain classification error that biases interactions toward zero; the same family (Claude) produced labels and, in two combinations, ratings; 12 comparisons without multiplicity correction; ~1.3 reviews per product, so product clustering is uninformative here.

## Human validation of the product labels (100 independent products)
Two coders, blind to LLM labels, after a calibration round on a different 100 products (calibration agreement kappa .27 / .42; those items are not used for validation).
- Inter-coder agreement (P101-P200, n=100): search/experience 97%, kappa .926 (95% CI .83-1.00); hedonic/utilitarian 94%, kappa .855 (.73-.95); both dimensions identical for 91 products.
- Nine disagreements resolved jointly by the coders (hair/beard care decided once, as utilitarian).
- LLM vs consensus: search/experience 92.0%, kappa .820 (95% CI .69-.93); hedonic/utilitarian 90.0%, kappa .758 (.61-.89).
- Error direction: LLM says experience where humans say search 8x (0x opposite); LLM says hedonic where humans say utilitarian 8x (2x opposite). **Correction:** an earlier message described this direction the other way round.
- Labels: `validation/product_label_validation_P101-P200.csv` (IDs and labels only; no listing text).
- Caveats: n=100; decision rules refined after the calibration round and adjudication decided after seeing disagreements; independence of the two coders is assumed, not verified.
