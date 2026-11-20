# Qualtrics 구현 안내서 (Study 2)

> **가져오기 파일과 더 단순한 구현법(Loop & Merge)은 `qualtrics/README.md`를 먼저 본다.** 그 방법을 쓰면 아래 §5의 셀별 Embedded Data 입력이 필요 없다.
> 응답자에게 보이는 문안은 `study2_survey_english.md`, 조건 배정과 수치는 `study2_survey_instrument.md` §4를 따른다. 이 안내서는 **제가 Qualtrics의 기능을 기억에 의존해 쓴 것**이라 메뉴 이름이나 옵션 위치가 다를 수 있다. 각 단계 끝의 **[확인]**은 미리보기나 테스트 응답으로 직접 확인할 지점이다. Prolific 연동 문구는 Prolific 연구 설정 화면의 안내와 같은지 대조한다.

## 0. 설계 요약 (무엇을 구현하는가)

| 요소 | 값 |
| --- | --- |
| 피험자 간 | 뉴스 항목 2종(사고 사례 / 중립), 50:50 |
| 피험자 내 | 시나리오 4개: C1(λ 2%, 정확도만), C2(2%, 병기), C3(6%, 정확도만), C4(6%, 병기) |
| 사례-셀 배정 | 라틴 방격 V1–V4 중 하나(균등), 제시 순서는 무선 |
| 문항 | 시나리오마다 Q1(이해 점검), Q2(선택), Q3(WTP 숫자 입력), Q4(추정 확률), Q5(품질 격차) |

라틴 방격 (사례를 셀에 배정):

| 버전 | C1 | C2 | C3 | C4 |
| --- | --- | --- | --- | --- |
| V1 | A | B | C | D |
| V2 | B | C | D | A |
| V3 | C | D | A | B |
| V4 | D | A | B | C |

## 1. 설문 흐름(Survey Flow) 전체 모양

위에서 아래 순서로 만든다.

```
1. Embedded Data: PROLIFIC_PID, STUDY_ID, SESSION_ID          (값은 URL에서 받아옴)
2. Block: Consent                                              (동의 안 하면 종료)
3. Block: Eligibility S1–S8
4. Branch: 부적격이면 → End of Survey (스크린아웃 처리)
5. Randomizer "Evenly Present" 1 of 2:                         (뉴스 항목, 피험자 간)
      Embedded Data news = incident   + Block: News_Incident
      Embedded Data news = control    + Block: News_Control
6. Block: GeneralProbability (3-C)
7. Randomizer "Evenly Present" 1 of 4:                         (라틴 방격 버전)
      Embedded Data version=V1, case_C1=A, case_C2=B, case_C3=C, case_C4=D
      Embedded Data version=V2, case_C1=B, case_C2=C, case_C3=D, case_C4=A
      Embedded Data version=V3, case_C1=C, case_C2=D, case_C3=A, case_C4=B
      Embedded Data version=V4, case_C1=D, case_C2=A, case_C3=B, case_C4=C
8. Randomizer "Randomly present 4 of 4" (제시 순서):
      Block: Scenario_C1, Scenario_C2, Scenario_C3, Scenario_C4
      (두 번째 시나리오가 끝난 뒤 A1 주의 점검을 넣는 방법은 §6)
9. Block: Covariates (N1–N3, E1–E3, PC1–PC4, R1, A2, P2)
10. Block: Ranking P3, Block: Industry/IP I1–I3
11. Block: Consistency C1, Demographics
12. Block: Debrief
13. End of Survey → Prolific 완료 URL로 리디렉션
```

**[확인]** 흐름의 순서가 위와 같은지, 각 Randomizer 안의 요소가 바르게 들어갔는지 Survey Flow 화면에서 눈으로 확인한다.

## 2. Prolific 연동

1. Survey Flow **맨 위**에 Embedded Data 요소를 추가하고 `PROLIFIC_PID`, `STUDY_ID`, `SESSION_ID` 세 필드를 값 없이 만든다.
2. Prolific에서 연구를 만들 때 설문 주소를 아래 형태로 입력한다(Prolific 안내 화면의 자리표시자와 같은지 확인).
   ```
   https://<귀하의 Qualtrics 주소>/jfe/form/SV_xxxxxxxx?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
   ```
3. 설문 맨 끝 End of Survey 요소에서 **Customize → Override Survey Options → Redirect to a URL**을 선택하고 Prolific이 알려 주는 **완료 URL**을 붙여 넣는다.
4. **스크린아웃**(부적격) 응답자의 처리 방식(보상, 별도 완료 코드)은 Prolific 도움말에서 현재 규칙을 확인하고, 결정한 대로 별도 End of Survey를 만든다. 앞서 확인한 규칙은 "스크린아웃 보상을 연구마다 설정(최소 $0.14)"이다.
5. 공유할 데이터에서는 `PROLIFIC_PID`를 삭제한다(동의문에서 익명이라고 했기 때문).

**[확인]** 테스트용 주소(`?PROLIFIC_PID=test123`)로 접속해서 응답 데이터에 `PROLIFIC_PID`가 기록되는지 본다.

## 3. 자격 분기(Branch) 만들기

자격 규칙(`screening_items.md`): **S1 ∈ {1–6} AND S3 ∈ {1, 2, 3} AND (S2 ≥ 3 OR S4 ≥ 3 OR S3 ∈ {1, 2}) AND S6 ≥ 2 AND S5 ≥ 2**. S1, S3 등은 선택지 순서 번호로 비교한다(선택지 번호가 문서의 순서와 같게 만들 것).

Survey Flow에서 Branch를 추가하고 **"부적격" 조건**을 만든다.
- 부적격 = **S1이 7 또는 8** OR **S3이 5** OR **S6이 1** OR **S5가 1**, OR **(S3이 3 AND S2가 1 또는 2 AND S4가 1 또는 2)**
- 위 조건을 Branch의 "If" 아래 **Add a Condition**으로 OR로 이어 붙이고, 그 아래에 End of Survey(스크린아웃)를 둔다.
- **S8은 조건에 넣지 않는다**(자격 기준이 아니며 모든 응답자가 계속한다).

**[확인]** 아래 5가지 경우로 미리보기를 해서 의도대로 분기하는지 본다: (1) 모두 적격, (2) S1=Other, (3) S3=I am not involved, (4) S6=Not involved, (5) S3=group member + S2=Individual + S4=None(→ 부적격).

## 4. 조건 배정(Randomizer)

- Randomizer 요소를 열고 **"Randomly present 1 of the following elements"**를 선택, **Evenly Present Elements**를 체크한다. 뉴스 항목(2개 요소)과 버전(4개 요소) 각각에 적용한다.
- 각 요소는 Embedded Data(`news`, `version`, `case_C1~C4`)와 필요하면 Block을 포함한다.
- **교차 균형**: 두 Randomizer는 서로 독립이라 8개 조합이 정확히 같은 수로 나오지는 않는다(기대 균형만 보장). 소규모 표본(N=200)이 신경 쓰이면 **Quotas**로 8개 조합(뉴스 × 버전)에 상한을 거는 방법이 있다. 다만 설정이 복잡해지니 사전 점검의 테스트 응답에서 분포를 먼저 보고 필요할 때 쓴다.

**[확인]** *Tools → Generate Test Responses*로 테스트 응답을 40개쯤 만들어(미리보기 데이터는 따로 삭제) 뉴스 2종과 버전 4종이 비슷하게 나오는지 본다. 테스트 데이터는 본 수집 전에 반드시 지운다.

## 5. 시나리오 블록 만들기

시나리오는 **셀 4개(C1~C4)마다 블록 1개**씩 만든다. 사례(A~D)에 따른 문구와 수치는 **Embedded Data를 파이프(piping)**해서 넣는다.

1. 사례별 수치를 Embedded Data로 저장해 둔다. Survey Flow 맨 위에 **사례 정보 표**(`study2_survey_english.md` §4-2)를 Embedded Data로 넣는다: 사례마다 `title_A`, `task_A`, `data_A`, `B_A`, `E_A`, `L_A`, `accL_A`, `accA_A`, `costL_A`, `costA_A`, `slidermax_A` … (A~D 각각).
2. 블록 `Scenario_C1`의 본문에서 사례 필드를 파이프한다. 사례 이름은 `${e://Field/case_C1}`이고, 사례 A의 값은 `${e://Field/B_A}`처럼 사례 코드가 붙은 필드다. **필드 이름 안에 다른 필드를 중첩해 파이프하는 것은 안 되므로**, 사례 4개 중 해당 사례의 값을 고르는 단계를 별도로 둔다. 가장 간단한 방법:
   - 버전을 정하는 Randomizer의 각 요소에서 **셀별 값을 바로 Embedded Data로 저장**한다(예: `title_C1`, `task_C1`, `data_C1`, `B_C1`, `E_C1`, `L_C1`, `accL_C1`, `accA_C1`, `costL_C1`, `costA_C1`, `slidermax_C1`, 그리고 C2~C4도 같은 방식으로). 버전 4개 × 셀 4개 × 11개 필드를 입력해야 해서 많지만 한 번만 만들면 된다. 엑셀로 표를 만들어 두고 복사해 넣으면 실수가 줄어든다.
3. 셀별 고정 값은 블록에 직접 적는다: C1은 λ=2%·정확도만, C2는 λ=2%·병기, C3은 λ=6%·정확도만, C4는 λ=6%·병기.
4. 본문 템플릿(`study2_survey_english.md` §4-1)의 `{B}`, `{E}`, `{L}`, `{acc_local}` 등을 해당 셀의 Embedded Data 파이프(예: `${e://Field/B_C1}`)로 바꾼다.
5. 성능 표는 **정확도만** 블록(C1, C3)과 **병기** 블록(C2, C4)이 다르다. 표는 Rich Content Editor의 표 기능이나 HTML로 만든다.

### Q3 지불 의사 (숫자 입력, 확정)
- 문제 유형 **Text Entry(한 줄)**을 쓰고 안내문에 범위를 명시한다: "Enter an amount in thousands of dollars, between 0 and {L/4}. For example, 120 means $120,000 per year."
- 상한은 사례마다 다르다(A 400, B 300, C 500, D 600). Loop & Merge에서는 `${lm://Field/13}`로 채우고, Embedded Data 방식이면 해당 셀의 `smax_Cx`를 파이프한다.
- 설정: **Validation → Content type = Number**, 최솟값 0, **Force Response**. 초기값은 비워 둔다.
- 분석: L/4를 넘는 입력은 L/4로 자르고 개수를 보고한다. WTP = 0은 `0.001 × L`로 대체한다(사전등록).

### 나머지 문항
- Q1: 객관식(단일), **선택지 순서 무작위(Randomize)**.
- Q2: 객관식(단일), 선택지 순서는 **고정 또는 무작위**를 정해 두고 응답에 기록(`study2_survey_english.md`는 "local model / cloud API" 순서로 씀). 사전등록은 순서를 규정하지 않았으니 **무작위로 해서 위치 효과를 없애는 것을 권한다.**
- Q4: 텍스트 입력, 검증(**Validation → Content type = Number**, 최소 0, 최대 100).
- Q5: 7점 척도(양 끝 라벨만).

## 6. 주의 점검과 이해 점검

- **A1**(시나리오 2와 3 사이): 시나리오 블록이 무선 순서로 나오므로 "두 번째와 세 번째 사이"를 고정하기 어렵다. 방법: A1을 별도 블록으로 만들고, 시나리오를 **2개씩 두 묶음**(블록 묶음 X: C1, C2 무작위 / 묶음 Y: C3, C4 무작위)으로 나눠 사이에 A1을 넣되 묶음 순서도 무작위로 한다. 이러면 셀의 순서가 완전 무작위가 아니라 "묶음 안 무작위"가 된다. 사전등록은 "순서 무작위"라고만 썼으니, 이 방식을 쓰면 **사전등록 문구에 "시나리오 순서는 묶음 안에서 무작위이며 묶음 사이에 주의 점검이 있다"를 추가**한다. 그 대안은 A1을 시나리오 전체가 끝난 뒤 공변량 블록에 두는 것이다(단 사전등록의 위치와 달라진다).
- 이해 점검(Q1)은 **오답이어도 설문을 멈추지 않는다**(제외는 분석 단계에서 사전등록 규칙으로 한다).
- 제외 판정(주의 점검, 이해 점검, 시간, 무성의 응답)은 **설문 안에서 하지 말고 데이터 정리에서** 한다(종속변수를 보기 전에 자동 규칙으로).

## 7. 설정(Survey Options)과 개인정보

- **Anonymize responses**: 켠다(동의문의 "anonymous"와 일치. IP와 위치 정보가 저장되지 않음).
- **Prevent Multiple Submissions**: 켠다(같은 사람의 중복 응답 방지. Prolific에서도 한 번만 참여하게 설정).
- **Progress bar**: 켜도 되지만 블록 수가 가변적이면 부정확할 수 있다.
- **Back button**: 끈다(응답 수정 방지).
- **Language**: English.
- **Timing**: 각 시나리오 블록 첫 페이지에 **Timing** 질문(숨김)을 넣어 시나리오별 체류 시간을 기록하거나, 최소한 `Duration (in seconds)` 변수를 쓴다. 사전등록의 시간 기준(중앙값의 1/3 미만 제외)에 필요.

## 8. 데이터 내보내기와 정리

- Qualtrics에서 **Data & Analysis → Export → CSV, "Use numeric values"**로 내보낸다. **Randomizer 표시 순서**(`FL_xx_DO`)와 Embedded Data(`news`, `version`, `case_C1~C4`)가 열에 포함되는지 확인한다.
- 분석용 변수를 만든다(사전등록 정의):
  - `lnWTP_s = ln( WTP / L )`, WTP가 0이면 `0.001 × L`로 대체(`L`은 사례별 값)
  - `S_i = 평균 lnWTP (λ=6%의 두 셀) − 평균 lnWTP (λ=2%의 두 셀)`
  - 로컬 선택 지시변수(Q2), 추정 확률의 초과분 `λ̂ − λ`(Q4)
  - 제외 플래그: A1, A2, 이해 점검 오답 수, C1 불일치, 소요 시간, 무성의 응답
- 공유용 데이터에서는 `PROLIFIC_PID`, 자유 응답, 위치 정보를 삭제한다.

## 9. 출시 전 점검표

- [ ] 미리보기 10회 이상: 뉴스 2종, 버전 4종, 셀 4종이 모두 나온다
- [ ] 모든 시나리오의 `{B}`, `{E}`, `{L}`, `{λ}`, 정확도, 비용이 파이프로 채워져 있고 `${e://...}`가 그대로 보이는 곳이 없다
- [ ] 사례 A~D 모두 Q3 안내문의 상한이 맞다(A 400, B 300, C 500, D 600)
- [ ] 사고 사례와 중립 뉴스가 한 번에 하나만 나온다
- [ ] 자격 분기 5가지 경우 확인
- [ ] 모바일(휴대폰) 미리보기에서 숫자 입력(숫자 자판), 표, 긴 문장이 잘 보인다
- [ ] Prolific 테스트 응답으로 `PROLIFIC_PID` 기록과 완료 리디렉션 확인
- [ ] 테스트 응답 데이터 삭제
- [ ] 영어 원어민 검수 완료
- [ ] 사전 점검 10명 → 설문 동결 → 사전등록 제출

## 10. 자주 생기는 문제

| 문제 | 원인과 해결 |
| --- | --- |
| 시나리오 본문에 `${e://Field/...}`가 그대로 보임 | Embedded Data가 Survey Flow에서 해당 블록보다 **앞에** 있어야 하고, 필드 이름의 철자가 같아야 한다. |
| 8개 조합 분포가 치우침 | Evenly Present를 켰는지, 두 Randomizer가 독립이라 생기는 자연스러운 편차인지 확인한다. Quotas가 필요할 수 있다. |
| Q3에 `$120`이나 `120,000`을 입력하면 막힘 | Number 검증 때문이다. 안내문의 "in thousands of dollars ... For example, 120"를 확인하고 필요하면 `(numbers only)`를 덧붙인다. |
| 사고 사례/중립 뉴스 길이 차이 | Qualtrics의 단어 수가 아니라 **실제 화면에서 읽는 시간**이 비슷한지 확인한다. |
| 모바일에서 표가 잘림 | 표 열을 줄이거나 항목 줄바꿈을 늘린다. |
