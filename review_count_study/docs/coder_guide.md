# 리뷰 텍스트 코딩 지침서 (코더용)

## 1. 이 작업은 무엇인가요?
온라인 상품 리뷰 한 건씩을 읽고, **리뷰가 어떻게 쓰였는가**를 정해진 항목에 따라 기록합니다. 기록은 AI(LLM) 코딩이 얼마나 정확한지 검증하는 기준으로 쓰이므로, 여러분의 판단이 곧 "정답"입니다.

**중요한 원칙**
- 상품이 좋은지 나쁜지가 아니라 **글이 무엇을 어떻게 말하는지**를 코딩합니다.
- 리뷰에 **쓰여 있는 근거**만 사용합니다. 상상, 추측, 상품 검색(구글 등)은 하지 않습니다.
- 별점과 좋아요 수는 일부러 보여 드리지 않습니다. 찾아보지 마세요.
- 다른 코더와 **코딩이 끝나기 전에는 시트 내용을 상의하지 않습니다.** (겹치는 리뷰로 코더 간 일치도를 재기 때문입니다.)

## 2. 준비물과 진행 방법
1. 받은 파일(`coder_A.csv` 또는 `coder_B.csv`)을 엑셀이나 구글 시트로 엽니다. CSV는 UTF-8이므로 엑셀에서는 "데이터 → 텍스트/CSV 가져오기"로 여는 것이 안전합니다.
2. 첫 행(`#ALLOWED_VALUES`)은 허용 값 안내입니다. 읽고 지워도 됩니다.
3. 각 행의 `text`를 읽고 오른쪽 칸을 채웁니다. 행 순서와 `review_id`는 **절대 바꾸지 마세요.**
4. 모든 칸에 값을 넣고 저장합니다(CSV로 저장). 칸이 비거나 허용 값이 아니면 병합 단계에서 오류가 납니다.
5. 소요 시간은 리뷰당 약 1–1.5분이고, 250건이면 4–6시간입니다. 피로가 쌓이면 일관성이 떨어지니 **한 번에 1시간 이내**로 끊어서 하세요.

### 시작 전 연습 (필수, 약 30분)
시트의 리뷰로 연습하지 말고 아래 **5절의 연습 문제**로 먼저 연습합니다. 코더 두 명이 각자 풀고, 정답과 다른 항목은 이유를 이야기해 기준을 맞춥니다. 연습 후에는 시트 작업이 끝날 때까지 시트 내용을 상의하지 않습니다.

## 3. 항목별 정의

| 칸 | 값 | 한 줄 정의 |
|---|---|---|
| `valid` | 1 / 0 | 읽을 수 있는 리뷰면 1. 비어 있거나 깨진 글자뿐이면 0 (0이면 아래 칸은 비워 둠) |
| `sentiment` | 1–5 | 글이 표현하는 **전체 평가**. 1 매우 부정, 3 중립·혼합, 5 매우 긍정 |
| `emotional_intensity` | 1–5 | 감정 표현의 **세기**. 1 사실만 서술, 5 매우 격정적 |
| `specificity` | 1–5 | **구체적 세부 정보**(제품명·기능·수치·시점·상황)의 양. 1 일반론뿐, 5 매우 구체적 |
| `informativeness` | 1–5 | 앞으로 살 사람에게 **도움이 되는 정보**의 양(장단점, 가격, 사용 조건). 1 없음, 5 매우 풍부 |
| `argument_balance` | 1–3 | 1 한쪽 면만, 2 약간 양면, 3 장점과 단점을 **둘 다 명시적으로** 서술 |
| `narrative` | 0 / 1 | 시간 순서가 있는 **개인 경험 이야기**가 있으면 1 |
| `explicit_recommendation` | 0 / 1 | **독자에게** 사라/가라/피하라고 직접 말하면 1 |
| `comparison` | 0 / 1 | 다른 제품, 업체, 이전 경험과 **명시적으로 비교**하면 1 |
| `dominant_emotion` | 6개 중 하나 | 가장 두드러진 감정 (아래 4절) |
| `notes` | 자유 | 판단이 어려웠던 이유 등 메모 (선택) |

### 항목별 판단 요령
- **sentiment**: 대상이 상품이든 배송이든 판매자든, 글 전체가 전하는 평가를 봅니다. 반어(풍자)는 **의도한 평가**로 코딩합니다("Great, it broke on day one" → 1–2).
- **emotional_intensity**: 느낌표, 대문자, 강한 감정어, 과장이 많을수록 높게 줍니다. 평가가 극단적이어도 담담하게 쓰였으면 낮습니다.
- **specificity vs informativeness**: 구체적(고유명, 숫자)이라고 해서 모두 유용한 정보는 아닙니다. 예를 들어 "I bought it on Tuesday at 3pm"은 구체적이지만 정보성은 낮습니다.
- **narrative**: "샀다 → 써 봤다 → 이런 일이 생겼다"처럼 사건이 순서대로 이어질 때만 1. 단순한 상태 설명("It's big and heavy")은 0.
- **explicit_recommendation**: "Never buying again"은 본인 결심일 뿐 독자에게 하는 말이 아니므로 0. "Don't buy this"나 "Highly recommend!"처럼 독자를 향하면 1.
- **comparison**: "Better than my old one", "unlike the other brand"처럼 비교 대상이 글에 나올 때 1.
- 점수가 애매하면 **중간값으로 도피하지 말고** 아래 앵커 예시에 더 가까운 쪽을 고릅니다.

### 앵커 예시
- specificity 1: "Great place, loved it." / 3: "The pasta was good and service was fast." / 5: "Ordered the truffle gnocchi ($24) at 7pm Friday; arrived in 10 min, sauce was salty but portion was big."
- informativeness 1: "Terrible!!!" / 5: "Battery lasts ~9h at 50% brightness, fan loud under load; fine for office work, not gaming."
- emotional_intensity 5: "ABSOLUTELY DISGUSTING!!! Worst night of my life!!!"

## 4. dominant_emotion 값
허용 값은 아래 6개뿐이고 **소문자**로 입력합니다.

| 값 | 쓰는 경우 |
|---|---|
| `joy` | 기쁨, 만족, 즐거움 |
| `anger` | 분노, 짜증, 불만 |
| `anxiety` | 불안, 걱정, 우려 |
| `sadness` | 슬픔, 실망, 아쉬움 |
| `surprise` | 놀람 |
| `none` | 뚜렷한 감정이 없거나 사실만 서술 |

- 여러 감정이 있으면 **가장 두드러진 하나**만 고릅니다.
- 애매하면 억지로 고르지 말고 `none`.
- 분석 단계에서 드문 감정이 합쳐지지만, **코더는 합치지 말고 6개로 구분**해서 입력합니다.

## 5. 연습 문제 (정답 확인용)
아래 정답은 기준 예시입니다. 점수 항목은 ±1 정도 차이는 정상이며, 이진 항목과 감정 값이 다르면 이유를 이야기해 보세요.

**연습 1** — "Terrible!!! Never buying again."
`valid 1 / sentiment 1 / emotional_intensity 4 / specificity 1 / informativeness 1 / argument_balance 1 / narrative 0 / recommendation 0 / comparison 0 / emotion anger`
이유: 구체 정보가 전혀 없고, "Never buying again"은 독자를 향한 권고가 아니라 0.

**연습 2** — "Bought these three weeks ago for $18. Battery lasts about 6 hours at medium brightness, fine for commuting. The case feels cheap and one hinge cracked after 10 days, but support replaced it in 2 days. I'd recommend it to anyone on a budget."
`valid 1 / sentiment 4 / emotional_intensity 1 / specificity 5 / informativeness 5 / argument_balance 3 / narrative 1 / recommendation 1 / comparison 0 / emotion none`
이유: 장단점을 모두 명시했고, 구매→사용→고장→교체의 시간 순서가 있으며, 독자에게 직접 권고했습니다. 감정 표현은 없어 none.

**연습 3** — "This is way better than the old model I had, which broke after a year. Love it!"
`valid 1 / sentiment 5 / emotional_intensity 3 / specificity 2 / informativeness 2 / argument_balance 1 / narrative 0 / recommendation 0 / comparison 1 / emotion joy`

**연습 4** — "Great, it stopped working on day one. Fantastic quality."
`valid 1 / sentiment 1 / emotional_intensity 3 / specificity 2 / informativeness 2 / argument_balance 1 / narrative 0 / recommendation 0 / comparison 0 / emotion anger`
이유: 반어입니다. 겉말은 긍정이지만 의도한 평가는 부정.

**연습 5** — "Package came late and the box was crushed. The item itself works fine though."
`valid 1 / sentiment 3 / emotional_intensity 1 / specificity 3 / informativeness 3 / argument_balance 3 / narrative 0 / recommendation 0 / comparison 0 / emotion none`
이유: 배송 불만과 상품 만족이 섞여 중립·혼합이고 양면이 모두 있습니다.

## 6. 자주 나오는 애매한 경우

| 상황 | 처리 |
|---|---|
| 영어가 아니거나 번역투 | 이해되는 만큼 같은 기준으로 코딩. 전혀 이해 못하면 `valid 0` + notes |
| 아주 짧은 글("Good") | 정상 코딩(대부분 specificity 1, informativeness 1) |
| 광고·링크·스팸 같은 글 | 글 내용 기준으로 코딩, 상품 평가가 전혀 없으면 sentiment 3, notes에 표시 |
| 리뷰가 상품이 아닌 판매자·배송만 다룸 | sentiment는 글이 전하는 평가로 코딩, informativeness는 독자에게 유용한 정도로 |
| 별점을 언급("5 stars") | 글에 있는 근거로 인정하되 sentiment만 반영 |
| 판단이 어려움 | 가장 가까운 값을 고르고 `notes`에 이유를 한 줄 적기 |

## 7. 제출과 이후 절차
1. 완료한 CSV를 **원본 이름 그대로**(`coder_A.csv`/`coder_B.csv`) 연구 책임자에게 보냅니다.
2. 연구팀이 두 시트를 병합하면 코더 간 일치도와 **불일치 목록**이 나옵니다.
3. 두 코더가 불일치 항목만 함께 보고 합의합니다(이때만 상의 가능). 합의 결과가 최종 정답으로 사용됩니다.
4. 일치도 기준: 0.67 미만이면 해당 항목의 정의를 고쳐 다시 코딩할 수 있습니다.

## 8. 비밀 유지
- 리뷰 원문은 Amazon 리뷰 데이터에서 온 것으로, **연구 목적 외 사용과 외부 공유를 금지**합니다.
- 시트를 클라우드, 메신저, 생성형 AI 서비스에 올리지 마세요.
- 작업이 끝나면 개인 기기의 사본을 삭제합니다.

---
문의: 연구 책임자 (판단 기준이 모호한 항목은 시트 작업 중에는 notes에 적고, 작업이 끝난 뒤 논의합니다.)
