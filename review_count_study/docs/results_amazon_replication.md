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
