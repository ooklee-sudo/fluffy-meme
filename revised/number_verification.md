# 원고 수치 검증 보고서

대상: `Manuscript_MISQ_Format_Final.docx` (39쪽). 근거: 사용자가 실행한 `run_all.bat`(999회), `rq123.py --only-rq3`(999회), 최초 `analyze.py` 출력, 키트의 `events.csv`와 `repo_relevance.csv`.

## 결과: 66개 수치 문장을 원문 그대로 대조
- 일치 65개, 불일치 1개(τ² 0.050 → 0.049로 수정함).
- Table 1 전체(19행 × 4열)를 코드 출력과 대조해 불일치 0. 주 수 합계 3,432, 릴리스 수 합계 2,456.
- 이벤트 38개(open-weights 22, OpenAI 6, Anthropic 6, Google 4)와 노출 수(11, 6, 6, 5)를 `events.csv`와 `repo_relevance.csv`에서 직접 세어 일치 확인. 이벤트 기간은 2023-07-18~2026-07-16.

## 이번 점검에서 고친 것
| 위치 | 이전 | 수정 |
|---|---|---|
| 5.2 풀링 hazard slope의 τ² | 0.050 (이전 실행값) | 0.049 (`rq123.py` 999회) |
| 5.6 릴리스 내용의 손 검수 | "3개가 fix, 나머지 9개" | "2개가 fix, 나머지 10개는 fix 아님(1개는 기여자 이름)" — 출력된 12개 중 `[FIX]` 표시는 trl, vLLM 2개뿐 |

## 검증하지 못한 것 (직접 확인 필요)
1. **4.1절 후보 저장소 수치:** Qwen2.5(140주 동안 릴리스 0), DeepSeek-V3(94주 동안 1), llama.cpp(188주 동안 185), "20개 수집 중 mlc-llm 제외". 현재 코드와 출력에 근거가 없습니다. llama.cpp의 185건은 제 기억과 달라 보입니다(빌드마다 릴리스를 올리는 저장소). 아래 명령으로 확인하세요.
   ```
   python collect.py QwenLM/Qwen2.5 deepseek-ai/DeepSeek-V3 ggml-org/llama.cpp mlc-ai/mlc-llm
   python -c "import json,glob; [print(f, len(json.load(open(f)))) for f in sorted(glob.glob('data/*/releases.json')) if any(k in f for k in ('Qwen','DeepSeek','llama.cpp','mlc'))]"
   ```
2. **5.2절 "Documented release policies":** 저장소 문서를 읽은 서술이며 코드가 없어 확인하지 못했습니다.
3. **4.1절의 "17개를 사전에 고정했다"는 절차 서술:** 수치가 아니라 연구 절차에 대한 주장이므로 저자가 직접 확인해야 합니다.

## 반올림과 출처 메모
- 핫픽스 비율 42.7% → "43 percent", 나이 1주 핫픽스 주 비율 0.365 → "36 percent", 나이 2~7주 4.5~7.8% → "5 to 8 percent".
- (b)와 (d)의 풀링값과 Table 1은 `rq123.py`에서, (a)와 (c)는 `spec_c.py`에서 가져왔습니다. 같은 (b)가 −0.0029(`rq123.py`)와 −0.0023(`spec_c.py`)로 약간 다른 것은 부트스트랩 시드 순서 차이입니다. 동등성 검정(5.6)의 (b)와 (d)는 `rq123.py`의 풀링 CI에서 SE를 역산했습니다.
- RQ3 wild bootstrap p값은 `--only-rq3` 실행값으로 통일했습니다(전체 실행과 ±0.02 차이).
- Table 1의 "Weeks"는 원고의 옛 값이며 코드는 첫 주(나이 계산 불가)를 빼서 1씩 작습니다. 합계는 3,432로 패널과 일치합니다.
- 3절의 식은 대수적으로 다시 유도해 일치 확인(T* = √(2RC/(cγμ)), x* = √(2RCμ/(cγ))).
