# 코드북: 리뷰 텍스트 특성 (LLM 코딩용)

코딩 단위는 **리뷰 1건**입니다. 제품/업체의 질이 아니라 **텍스트가 어떻게 쓰였는가**를 코딩합니다.
별점·작성자·업체 정보는 LLM에게 제공하지 않습니다(텍스트만 제공 → 통제변수와의 오염 방지).

| 변수 | 유형 | 범위 | 정의 |
|---|---|---|---|
| `sentiment` | 순서형 | 1–5 | 텍스트가 표현하는 전반적 평가. 1=매우 부정, 3=중립/혼합, 5=매우 긍정 |
| `emotional_intensity` | 순서형 | 1–5 | 감정 표현의 강도(느낌표, 강한 수식어, 감정어). 1=사실적·무감정, 5=매우 격정적 |
| `specificity` | 순서형 | 1–5 | 구체적 세부 정보(고유 메뉴/기능명, 수치, 시점, 상황)의 밀도. 1=일반론만, 5=매우 구체적 |
| `informativeness` | 순서형 | 1–5 | 독자의 구매/방문 결정에 유용한 정보(장단점, 가격, 사용 조건)의 양. 1=없음, 5=매우 풍부 |
| `argument_balance` | 순서형 | 1–3 | 1=한쪽 면만, 2=약간 양면, 3=장점·단점을 모두 명시적으로 서술 |
| `narrative` | 이진 | 0/1 | 시간 순서의 개인 경험담(이야기 구조)이 있으면 1 |
| `explicit_recommendation` | 이진 | 0/1 | 독자에게 구매/방문/회피를 직접 권고하면 1 |
| `comparison` | 이진 | 0/1 | 다른 제품/업체/이전 경험과 명시적으로 비교하면 1 |
| `dominant_emotion` | 범주형 | joy, anger, anxiety, sadness, surprise, none | 가장 두드러진 감정. 뚜렷하지 않으면 `none` |

## 코딩 규칙
1. 텍스트에 **근거가 있는 것만** 코딩한다. 추론/상상으로 채우지 않는다.
2. 반어/풍자는 의도된 평가 기준으로 `sentiment`를 코딩한다.
3. 언어가 영어가 아니어도 동일 기준 적용. 판독 불가(빈 텍스트, 깨진 문자)는 `valid=false`.
4. 점수 앵커: 애매하면 중간값(3)이 아니라 **아래 앵커 예시와 가장 가까운 쪽**을 고른다.

## 앵커 예시
- `specificity=1`: "Great place, loved it."
- `specificity=3`: "The pasta was good and service was fast."
- `specificity=5`: "Ordered the truffle gnocchi ($24) at 7pm Friday; arrived in 10 min, sauce was salty but portion was big."
- `informativeness=1`: "Terrible!!!"
- `informativeness=5`: "Battery lasts ~9h with brightness at 50%, but fan is loud under load; fine for office work, not for gaming."
- `emotional_intensity=5`: "ABSOLUTELY DISGUSTING!!! Worst night of my life!!!"

## 신뢰도 검증 프로토콜
- 층화 무작위 300–500건을 인간 2인이 독립 코딩 → 인간 간 일치도(Krippendorff's α, 순서형은 ordinal)
- LLM vs 인간 합의값: 순서형은 가중 κ(quadratic) 및 Spearman, 이진/범주형은 Cohen's κ
- 기준: α·κ ≥ 0.67 잠정 허용, ≥ 0.80 권장 (Krippendorff 기준). 미달 변수는 정의·앵커 수정 후 재코딩
- 프롬프트 민감도: 문항 순서/표현을 바꾼 변형 2종으로 재코딩해 일치도 보고
- 교차 모델: 서로 다른 LLM 2종 이상으로 코딩해 일치도 보고
