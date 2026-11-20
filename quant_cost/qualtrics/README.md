# Qualtrics 가져오기 파일 (Study 2)

> **이 파일들은 Qualtrics 안에서 한 번도 시험하지 못했다.** 생성한 환경에는 Qualtrics 접속 권한이 없다. 내부 일관성(라틴 방격, 열 개수, 수치, 손익분기 λ* = 4%)만 코드로 검증했다. **새 테스트 설문에 먼저 가져와 보고** 문제가 있으면 오류 메시지를 알려 달라. 메뉴 이름은 기억에 의존했으니 화면과 다르면 [확인] 표시를 참고해 비슷한 메뉴를 찾는다.
> 상위 안내는 `../qualtrics_guide_study2.md`(흐름과 설정 전반), 영어 문안의 근거는 `../study2_survey_english.md`.

## 파일

| 파일 | 용도 |
| --- | --- |
| `import_questions.txt` | 정적 문항(동의, 자격 S1–S8, 소개, 뉴스 2종, 일반 확률, 시나리오 문항 Q1~Q5 틀, 주의 점검, 공변량, 인구통계, 해설) |
| `loop_merge_V1.tsv` … `V4.tsv` | 라틴 방격 버전별 Loop & Merge 표(행 4개 = 셀 C1~C4, 열 13개) |
| `scenario_body.html` | 시나리오 본문(HTML). `${lm://Field/n}`로 표의 값을 채운다 |
| `field_map.md` | 열 번호가 무엇인지 |
| `build_assets.py` | 위 파일을 만드는 코드(수치를 바꾸면 여기서 다시 생성) |

수치를 바꿀 때는 `build_assets.py`의 `CASES`를 고치고 `python quant_cost/qualtrics/build_assets.py`로 다시 만든다.

## 만드는 순서

### 1. 문항 가져오기
1. Qualtrics에서 새 설문(Blank survey)을 만든다. 이름: Study2_test.
2. **Import questions from → TXT/Word 파일**(Advanced Format)로 `import_questions.txt`를 가져온다. **[확인]** 블록이 13개, 문항이 39개 생겼는지, 선택지가 문서와 같은지 본다. 가져오기가 실패하면 오류가 가리키는 줄을 알려 달라(그 경우 블록별로 나눠 가져오거나 직접 만든다).
3. 가져온 뒤 확인: 동의 문항에서 "I do not agree"를 고르면 설문이 끝나도록 **Survey Flow**에서 분기를 만든다(§3).

### 2. 시나리오 블록 4개(Loop & Merge)
1. 블록 `Scenario_TEMPLATE`의 첫 문항(ScenarioText)을 열어 **HTML 보기**로 `scenario_body.html` 전체를 붙여 넣는다.
2. 블록을 **세 번 복사**해서 이름을 `Scenario_V1`, `Scenario_V2`, `Scenario_V3`, `Scenario_V4`로 바꾼다.
3. 각 블록에서 **Block Options → Loop & Merge → Static**을 켜고 해당 버전의 `loop_merge_Vn.tsv`를 표에 붙여 넣는다(엑셀에서 복사해 붙여 넣는 방식). 열 13개, 행 4개가 되어야 한다. **[확인]** 표에 Field 1~13이 보인다.
4. 같은 화면에서 **Randomize loop order**(반복 순서 무작위)를 켠다. 문서에 "Scenario n of 4"의 n은 `${lm://CurrentLoopNumber}`로 채우는데, 이 값이 제시 순서와 같은지 **[확인]**한다.
5. 가져온 **Q3**에 숫자 검증과 Force Response를 설정한다(아래 "Q3" 참조).

### 3. Survey Flow
`../qualtrics_guide_study2.md` §1의 흐름대로 만든다. 이 가져오기 파일에서는 시나리오 부분이 다음과 같이 단순해진다.

```
Randomizer: Randomly present 1 of 4, Evenly Present Elements
   ├ Embedded Data: version = V1  +  Block: Scenario_V1
   ├ Embedded Data: version = V2  +  Block: Scenario_V2
   ├ Embedded Data: version = V3  +  Block: Scenario_V3
   └ Embedded Data: version = V4  +  Block: Scenario_V4
```
`case_C1~C4` 같은 셀별 Embedded Data는 **필요 없다**(표의 2열에 사례 코드가 있고 응답 데이터에 반복 번호가 접두어로 붙는다). 뉴스 항목(`News_Incident`, `News_Control`) Randomizer, 자격 분기, Prolific 필드, End of Survey 리디렉션은 안내서의 §2, §3, §4를 따른다.

### 4. 직접 만들어야 하는 것
| 항목 | 내용 |
| --- | --- |
| Q3 (WTP) 설정 | 가져온 문항에 Number 검증(최소 0)과 Force Response |
| P3 순위 | **Rank Order** 문항: 상위 3개 요소를 고르고 순위를 매김. 항목 6개(`../study2_survey_english.md` §5) |
| C1 일관성 | S1, S2를 다시 묻는 문항(같은 선택지) |
| 국가 | 인구통계 블록에 거주 국가 드롭다운 |
| Timing | 시나리오 블록에 숨김 Timing 문항(선택) |
| 선택지 무작위 | Q1과 Q2에서 **선택지 순서 무작위(Randomize)**를 켠다 |
| 강제 응답 | Q2, Q4, S1~S8에 Force Response |
| Q4 검증 | Content type = Number, 최소 0, 최대 100 |
| 자격 분기와 스크린아웃 | `../qualtrics_guide_study2.md` §3 |
| A1 위치 | 가져온 `AttentionCheck_A1` 블록을 **시나리오 4개가 끝난 뒤**에 둔다(루프 안에서는 "2번째와 3번째 사이"를 고정할 수 없다). 사전등록은 A1의 위치를 규정하지 않았다 |

### Q3 (지불 의사): 숫자 입력으로 확정
- Q3는 `import_questions.txt`에 **텍스트 입력 문항으로 포함**되어 있다(안내문의 상한은 `${lm://Field/13}` = L/4).
- 가져온 뒤 Q3에 설정한다: **Validation → Content type = Number**, 최솟값 0, **Force Response**. 응답자가 `$`나 쉼표를 넣으면 검증에서 막힐 수 있어, 안내문에 "숫자만 입력"을 두려면 문구 끝에 `(numbers only)`를 붙여도 된다.
- 단위는 천 달러다(예: 120 = $120,000). 안내문에 예시가 있다.
- 분석에서는 L/4를 넘는 입력을 L/4로 자르고 개수를 보고한다(사전등록 문구에 반영됨).

## 확인 점검표

- [ ] TXT 가져오기에서 블록 13개, 문항 39개
- [ ] 시나리오 4개 블록 모두 표 13열 4행, 반복 순서 무작위
- [ ] 미리보기에서 본문에 `$80k`처럼 달러 표시가 나온다. **`$$80k`로 보이면** `scenario_body.html`의 `<b>$${lm://Field/6}k</b>`를 `<b>&#36;${lm://Field/6}k</b>`로 바꾼다(`$`를 HTML 코드로 쓰는 방법)
- [ ] 셀 C1, C3에는 비용 행이 없고 C2, C4에는 "Cost per 1,000,000 correct answers" 행이 있다
- [ ] V1~V4 각각 미리보기: 사례 순서가 라틴 방격과 같다(V1: A, B, C, D / V2: B, C, D, A / V3: C, D, A, B / V4: D, A, B, C)
- [ ] 뉴스 항목이 한 번에 하나만 나온다
- [ ] 테스트 응답으로 분포 확인 후 테스트 데이터 삭제
