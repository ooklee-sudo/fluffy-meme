# 시나리오 블록 직접 만들기 (가져오기가 안 될 때)

> 문항 6개(본문 + Q1~Q5)만 직접 만들면 된다. 메뉴 이름은 Qualtrics 화면과 다를 수 있다. 문구는 아래를 **그대로 복사**한다. 영어 문안의 근거는 `../study2_survey_english.md`.

## 0. 준비
1. 새 설문을 만들고 블록 이름을 `Scenario_V1`로 한다(블록 제목을 눌러 이름 변경).
2. 문항은 아래 순서로 한 블록 안에 만든다: **ScenarioText → Q1 → Q2 → Q3 → Q4 → Q5**.
3. 모든 문항에서 **Add Question 옵션 → Force Response(응답 강제)**를 켠다(ScenarioText 제외).
4. 문항마다 **Data Export Tag(데이터 내보내기 이름)**를 ScenarioText, Q1, Q2, Q3, Q4, Q5로 바꾼다(문항 옵션 → Question ID/Data export tag).

## 1. ScenarioText (Text / Graphic)
- 문제 유형: **Text / Graphic**(설명 텍스트)
- 문항 본문 편집창에서 도구 모음의 **소스 보기**(`<>` 또는 "Source")를 열고, `scenario_body.html` 파일의 **전체 내용**을 붙여 넣는다(메모장으로 열어 전체 복사).
- 파일 위치: `C:\Users\ookle\study2_qualtrics\scenario_body.html`

## 2. Q1 이해 점검 (Multiple Choice, 단일 선택, 세로)
**문항 본문**
```
In this scenario, what is the yearly chance that personal data is exposed through the cloud vendor?
```
**선택지 (4개, 이 순서로 입력)**
```
2%
6%
10%
20%
```
설정: **Randomize choices(선택지 무작위)** 켜기.

## 3. Q2 선택 (Multiple Choice, 단일 선택)
**문항 본문**
```
Which option would you choose for the coming year?
```
**선택지 (2개)**
```
The local model
The cloud API
```
설정: **Randomize choices(선택지 무작위)** 켜기.

## 4. Q3 지불 의사 (Text Entry, 한 줄)
**문항 본문** (소스 보기에서 붙여 넣으면 줄바꿈과 이탤릭이 적용된다. 소스 보기를 쓰지 않으려면 두 문단을 따로 입력해도 된다)
```
How much would you be willing to pay per year to eliminate the exposure risk of the cloud API altogether, that is, to be certain that no personal data is exposed through a vendor?<br><br><i>Enter an amount in thousands of dollars, between 0 and ${lm://Field/13}. For example, 120 means $120,000 per year.</i>
```
설정: **Validation → Content type = Number**, 최솟값 0, **Force Response**. 한 줄 텍스트 입력.

## 5. Q4 추정 확률 (Text Entry, 한 줄)
**문항 본문**
```
In your own judgment, what is the chance per year that personal data is exposed through the cloud vendor in this scenario? Enter a number from 0 to 100 (%).
```
설정: **Validation → Content type = Number**, 최솟값 0, 최댓값 100, **Force Response**.

## 6. Q5 품질 격차 (Multiple Choice, 단일 선택, 가로 7점)
**문항 본문**
```
How large is the local model's quality disadvantage compared with the cloud API in this scenario?
```
**선택지 (7개, 이 순서로)**
```
1 = Not large at all
2
3
4
5
6
7 = Extremely large
```
선택지 순서는 **무작위로 하지 않는다**(척도).

## 7. 블록 복사와 Loop & Merge
1. `Scenario_V1` 블록을 **세 번 복사**하고 이름을 `Scenario_V2`, `Scenario_V3`, `Scenario_V4`로 바꾼다.
2. 각 블록의 **Block Options → Loop & Merge → Turn on → Static**을 켜고 해당 번호의 `loop_merge_Vn.tsv` 전체를 붙여 넣는다(`C:\Users\ookle\study2_qualtrics\` 폴더). 행 4개, 열 13개여야 한다. 열이 모자라면 **Add Field**로 13개까지 늘린 뒤 다시 붙여 넣는다.
3. **Randomize loop order** 옵션이 있으면 켠다.
4. 미리보기로 확인: `Scenario 1 of 4: Sorting customer inquiries`처럼 값이 채워지고, 금액이 `$80k`로 나오고, 성능 표가 보이고(어떤 시나리오에는 비용 행이 있고 어떤 시나리오에는 없다), Q3 안내문의 상한이 숫자로 나온다.

## 8. 나머지 문항
시나리오 블록 외의 문항(동의, 자격 S1~S8, 소개, 뉴스, 공변량, 해설)은 `../study2_survey_english.md`의 영어 문안을 직접 입력하거나, 가져오기가 되는 경우 `import_questions.txt`를 쓴다. 우선 시나리오 블록이 제대로 동작하는지 확인한 뒤 나머지를 만든다.
