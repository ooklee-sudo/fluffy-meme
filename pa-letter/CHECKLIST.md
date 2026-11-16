# 투고 전 확인 목록 (Political Analysis Letter)

`letter.tex`에서 빨간 굵은 글씨 `\chk{...}`로 표시된 곳이 아래 항목입니다. 모두 해결한 뒤 `\chk`를 검색해 남은 것이 없는지 확인하세요.

## A. 원 자료에서 채워야 할 숫자

| # | 위치 | 내용 | 비고 |
|---|---|---|---|
| A1 | 3절 본문, Table 1 Panel B | v2 각 실행(opus, sonnet, haiku, sonnet repeat, majority)의 escalation 라벨 수 | 원 원고 Table 2의 "Escalation predicted" 열. PDF 추출에서 누락. 본문에는 "73–85"로만 나옴 |
| A2 | 3절 본문 | escalation 라벨 수 범위 `[63]`–`[85]` | 63은 model 1(22/63). 85는 v2 최댓값으로 추정 |
| A3 | Table 1 Panel A | Model 1과 두 번째 실행의 κ = 0.74가 계산된 게시물 수 | 원고에는 "human-validation sample"로만 표기 |
| A4 | Table 2 | Human mixed / other 사건 수: Model 1 = 7 / 3, v2 majority = 12 / 5 | **역산한 값.** 식 (2)의 각 항과 평균이 모두 원고와 일치하지만 원 자료로 확인 필요 |
| A5 | 6절 | DSL에 쓴 "five model runs"가 어느 실행인지 | model 1 + v2 4회인지, model 2 포함 여부 |
| A6 | 2절 | 사람 코더가 191개 전체를 codebook v2로 코딩했는지 | 원고상 2라운드(61개)와 3라운드(130개) 모두 v2. 사람 간 κ = 0.67은 원고 Table 1의 191개 값 |

## B. SI 번호 (SI를 만든 뒤 채우기)

| # | 위치 | 내용 |
|---|---|---|
| B1 | 5절 본문, Table 2 주석 | de-escalation 분해표 (원 원고 Table 4 Panel B) |
| B2 | Figure 2 주석 | PPI 시뮬레이션 그림 |

## C. 그림 제작

| # | 내용 |
|---|---|
| C1 | Figure 1: 라벨 세트별 평균과 95% CI. 사양은 tex 파일의 placeholder에 적혀 있음 |
| C2 | Figure 2: 2×2 시뮬레이션 그림. PPI는 SI로 |

## D. 참고문헌 서지 정보 확인 (`references.bib`의 `note = {VERIFY}`)

| # | 문헌 | 확인할 것 |
|---|---|---|
| D1 | Fong & Tyler (2021), *Political Analysis* | 권·호·쪽 |
| D2 | Knox, Lucas & Cho (2022), *Annual Review of Political Science* | 권·쪽 |
| D3 | TeBlunthuis, Hase & Chan (2024), *Communication Methods and Measures* | 권·호·쪽 |
| D4 | Gwet (2008), *British Journal of Mathematical and Statistical Psychology* | AC1 원전으로 적절한지, 서지 |

나머지 문헌은 원 원고 참고문헌을 그대로 옮겼거나(Aigner, Angelopoulos, Bound, Cohen, Egami, Gilardi, Grimmer, Hu, Lewbel, Mahajan, Ziems) 잘 알려진 서지(Gelman & Stern 2006, Yang et al. 2018)입니다.

## E. 방법·윤리 관련

| # | 내용 |
|---|---|
| E1 | LLM 실행 환경(Claude Code 서브에이전트, 기본 sampling 설정)을 SI에 사실대로 기술. 가능하면 API에서 temperature와 모델 스냅샷을 고정해 다시 실행 |
| E2 | Data Availability: Political Analysis Dataverse에 올릴 자료를 정리. Dukascopy 틱 데이터를 재배포할 수 있는지 약관 확인 |
| E3 | 생성형 AI 사용 고지를 저널 정책에 맞게 작성 (원고 작성·코드 보조 사용 여부) |
| E4 | 익명 심사: 코더 소속("authors' department")은 본문에서 뺐음. 게재 확정 후 복원 |

## F. 저널 가이드라인

| # | 내용 |
|---|---|
| F1 | Letter 단어 한도(약 4,000단어로 알고 있음)와 참고문헌·표·초록이 단어 수에 포함되는지 |
| F2 | 표·그림 개수 제한, 초록 길이 제한 |
| F3 | 인용 스타일(현재 `apalike`로 임시 설정) |

## G. 선택 사항

| # | 내용 |
|---|---|
| G1 | 두 번째 사례(2017–21 관세 트윗, 원 원고 Appendix E.5) 추가. 넣으면 Introduction 넷째 단락, 7절 한계 문장, 초록 수정 |
| G2 | 5절의 "precision does not predict bias" 주장에 대해 예상되는 반론: Model 1에서는 오염 사건 효과를 0으로 가정한 감쇠 계산이 우연히 0.17과 일치. v2 majority에서는 맞지 않는다(0.30 × 0.44 ≈ 0.13 대 실제 0.32)는 문장을 넣을지 |
