# 투고 전 확인 목록 (Political Analysis Letter)

`letter.tex`에서 빨간 굵은 글씨 `\chk{...}`로 표시된 곳이 아래 항목입니다. 모두 해결한 뒤 `\chk`를 검색해 남은 것이 없는지 확인하세요.

## A. 원 자료에서 채워야 할 숫자

원 원고 PDF의 Table 2와 Table 4에서 확인해 모두 채웠습니다 (2026-11-17).

| # | 위치 | 채운 값 | 출처 |
|---|---|---|---|
| A1 | Table 1 Panel B, escalation 라벨 수 | v2 opus 78, v2 sonnet 85, v2 haiku 76, v2 sonnet repeat 73, v2 majority 77 | 원 원고 Table 2 "Escalation predicted" |
| A2 | 3절 본문 범위 | 63–85 (model 1 63, v2 최댓값 85) | 같음 |
| A3 | Table 1 Panel A, κ = 0.74의 게시물 수 | 150 (1라운드 검증 표본; 표 주석에 명시) | 원 원고 2.2절, Appendix C |
| A4 | Table 2 mixed / other 사건 수 | Model 1 = 7 / 3, v2 majority = 12 / 5 (역산값과 일치) | 원 원고 Table 4 |

남은 확인 사항:

| # | 위치 | 내용 |
|---|---|---|

## B. SI (`si.tex`, `si.docx`)

SI를 만들고 본문의 SI 번호를 채웠습니다: de-escalation 분해표 = Table S3, PPI 그림 = Figure S1, LLM 실행 환경 = Section S1.

검증 부분표본의 사건 수 분포는 SI Table S4로 계산해 넣었고(초기하분포, 정확 계산), 관세 사례(S8)는 삭제했습니다.

SI 안에 남은 확인 사항 (`si.tex`의 `\chk`):

| # | 위치 | 내용 |
|---|---|---|
| B1 | S1.1 | API로 다시 실행한다면 그 설정과 결과 |
| B2 | S5 | DSL의 "five model runs" 구성 (본문 A5와 같음) |
| B6 | S7 | 분석 계획 전체 목록을 공개·인용할지 |

## C. 그림

원 결과 파일이 없어 Figure 2와 SI Figure S1·S2는 넣지 않기로 했습니다. 해당 결과는 본문 6절과 SI S5·S6에 숫자로 남아 있습니다.

| # | 내용 |
|---|---|
| C1 | Figure 1: 완료 (`figures/figure1.pdf`, `.png`, 스크립트 `figures/make_figure1.py`). 모델 라벨 세트별 평균의 CI는 원 원고에 없어 사람 라벨 CI만 표시. 모델별 CI를 계산하면 스크립트에 추가 |

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
| F1 | 단어 한도: Letter는 2,500단어 (참고문헌·제목·초록·감사의 글 제외). 본문 1,982단어 (Data Availability·AI 고지 포함), 표·캡션까지 2,465단어 |
| F2 | 투고 양식: Figures 1, Tables 2 |
| F3 | 인용 스타일(현재 `apalike`로 임시 설정) |

## G. 선택 사항

| # | 내용 |
|---|---|
| G2 | 5절의 "precision does not predict bias" 주장에 대해 예상되는 반론: Model 1에서는 오염 사건 효과를 0으로 가정한 감쇠 계산이 우연히 0.17과 일치. v2 majority에서는 맞지 않는다(0.30 × 0.44 ≈ 0.13 대 실제 0.32)는 문장을 넣을지 |
