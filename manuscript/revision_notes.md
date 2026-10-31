# 원고 전체 읽기 후 수정 (최종본: Safety_Stock_AOR_final.docx)

## 이번에 고친 것

**누락·불일치**
- **WildChat 실제 도착 분석이 본문에 없었음** → 5.5절에 새 문단, 4.3·4.5·5.3·6.3절·부록 B·결론·서론에 반영. 공개 자료는 6종에서 7종으로. 참고문헌(Zhao et al. 2024, arXiv로 서지 확인) 추가.
- 5.7절의 재현 실험이 서론·4.1·4.2·5.1·5.2·6.1·6.2·6.3·결론과 어긋나던 문장 정리(예: "자기 심판을 시험하지 않았다" → "5.7절에서 시험", "연관이 약했다" → "중간 정도").
- 5절 맨 앞에 "5.1~5.6은 첫 표본, 5.7은 재현"이라는 안내 문단 추가.

**오류**
- 명제 5(c): 가장 큰 최소화점만 단조라고 썼는데 표 4는 작은 쪽을 보고했음 → **작은 쪽과 큰 쪽 모두 비감소**(Topkis)로 수정, 증명도 맞춤.
- 5.7절 첫 문단의 비문(쉼표로 이어진 세 항목) 수정, "두 가지 세부 사항" → "세 가지"로 정정.
- 문단이 문장 중간에서 잘린 곳 병합("this replay confirms / Proposition 2…", "By / Proposition 3…").
- 5.5절 소제목(Service incidents, Dated hallucination cases)이 앞 문단 끝에 붙어 있던 것을 각 문단의 머리말로 이동.
- 표 10 주석 "answer.✗indicates" 띄어쓰기, 참고문헌 정렬(Cox 1955가 Cox & Isham 1980보다 앞) 및 형식(Ji, Lewis, Zheng, Lin의 "AI- Human").

**재현성 (정직성)**
- 표 5의 출처를 실제 코드(econ_dependence.py)로 정정. 표 1~4·6·7과 명제 4·5의 수치를 다시 계산해 일치함을 확인하는 check_tables.py 추가(모두 통과).
- 부록 D: 새 스크립트 목록 추가. **원 파이프라인 스크립트(run_experiment.py, econ_tables.py, paper_tables.py 등)는 제가 작업한 파일에 없어서** 존재를 확인할 수 없음 → 본문에 "투고 전 삭제할 편집자 메모"를 넣어 두었으니 확인 후 지우세요.

## 확인했으나 고치지 않은 것
- 표 1~4, 6, 7과 서론·초록의 수치는 모두 재계산으로 일치. 증명 논리에 오류 없음.
- 표 1·6·7 주석의 "paper_tables.py / econ_tables.py"는 원 저자의 스크립트라 그대로 둠.

# 수정 내역 (Safety Stock for Machine Error → Annals of Operations Research 투고용, 초점 축소판)

## 0. 초점 축소

기여를 **'의존적 방어층 + 과산포 하에서의 용량 결정'** 하나로 좁혔습니다.

- 남긴 것: 명제 1(푸아송 용량), 2(과산포), 3(솎아내기), 4(의존성 경계), 5(최적 깊이·요소 대체), 6(서비스 수준↔부족 비용, 구 명제 7).
- 뺀 것(후속 연구로 6.3절에 한 줄 언급): 유형별 실패 모형(구 명제 6, 3.6절, 5.7절, 표 4·C2·C3, 부록 B의 해당 단락), 검토자 주의력 도덕적 해이(구 명제 8, 3.8절, 표 E4, 2.6절, 6.1·6.2·6.3절의 관련 문장).
- 함께 정리한 것: 초록·서론의 기여 목록·결론 재작성, 표 번호 재부여(표 1-10), 명제·절 번호와 상호참조 갱신, 사용처가 사라진 참고문헌(Hawkes, Holmström, Parasuraman, Watson, PatSnap, 특허) 삭제. 원고가 약 56쪽에서 36쪽(Word 기준)으로 줄었습니다.

## 0-b. OR 문헌 추가 (15편, Crossref로 제목·권·호·쪽수 확인)

- 2.1절을 3단락으로 확장: 뉴스벤더·용량 관리(Gallego & Moon 1993; Van Mieghem 2003), 콜센터 인력배치(Halfin & Whitt 1981; Borst et al. 2004; Gans et al. 2003; Aksin et al. 2007; Harrison & Zeevi 2005), 도착률 불확실성(Avramidis et al. 2004; Jongbloed & Koole 2001; Whitt 2006; Steckley et al. 2009; Bassamboo et al. 2010).
- 2.5절에 신뢰성 문헌 추가: 다중버전 소프트웨어의 동시 고장(Knight & Leveson 1986; Eckhardt & Lee 1985; Littlewood & Miller 1989).
- 서론 기여 문단에 위 두 흐름과의 관계를 한 문장 추가.

## 0-e. 자기 심판 문제 검증 — 다른 계열의 큰 판정 모델 (5.7절 갱신)

- Llama-3.3-70B(메타), Gemma-3-27B(구글)를 OpenRouter로 실행(약 6,000건, 비용 1달러 미만).
- **결과가 로컬 판정 모델과 크게 다름:** Gemma 청산율 54~69%/오차단 2~6%, Llama 78~86%/10~14%. 독립 예측 대비 배율 Gemma 1.6~2.0, Llama 2.5~3.3(라우팅 시 2.1~2.5, 3.8~5.0). 라우팅 효과가 재현되고 오히려 더 큼.
- 의존성은 판정 모델이 생성 모델과 같아서 생긴 것이 아님. 배율이 청산율과 함께 커지는 것은 명제 4(b)가 예측한 대로.
- **"판정 모델은 본전을 못 뽑는다"는 일반화 불가:** 약한 로컬 판정은 절감이 $0, 강한 외부 판정은 하루 $40~$669(정답 오염 $100 가정; 6건 중 3건에서 구간이 0을 제외). 5.7절·한계·6.2절을 그에 맞게 수정.
- 결과를 본 뒤에 한 것: 응답 파싱 규칙 보강(줄바꿈·마크다운 처리), 외부 판정 추가, 비용 비교 스크립트. 모두 DEVIATIONS.md에 기록. 초록 수치는 "1.2~3.3배(층의 청산율이 높을수록 커짐)"로 변경.

## 0-d. 재현 실험(held-out) 반영 — 새 5.7절, 표 12

- 새 표본 1,000문항, 같은 3개 생성기·L1·L2, 설정은 실행 전에 커밋(heldout_validation/PREREG.md).
- **재현됨:** L2 용량 감소 84~96%, 오차단율 19~75%, L2·L3 상관 φ=0.18/0.08/0.18, 독립 예측 대비 1.24~1.33배(구간이 1을 제외).
- **재현 안 됨:** 라우팅 효과(1.9~2.3배), L3 단독 수치(판정 프롬프트를 다시 써야 해서 비교 불가), Qwen0.5B의 오차단율(15.1% → 24.0%).
- **두 번째 판정 모델(SmolLM2-1.7B)은 쓸모없음:** 호출의 91~96%가 2초 초과, 느린 판정을 인정하면 99%를 차단(정답 포함). 자기 심판 문제는 해결되지 않았다고 본문에 명시.
- 본문 수치 갱신: 용량 감소 78~96%, 오차단 15~75%, 독립 예측 대비 1.2~1.6배. 한계 문단과 부록 D 수정.
- 결과를 본 뒤 정한 두 가지(UNSUPPORT 접두 분류, 느린 판정 인정 탐색 분석)는 본문과 heldout_validation/DEVIATIONS.md에 기록.

## 0-c. 명제 4·5 강화 (이론 기여 보강)

**명제 4 (의존성)** — 기존: 프레셰-본페로니 경계 + (양의 연관 시) 곱 공식이 하한.
- (a) 경계가 **날카로움**(구간 안의 모든 값이 달성 가능)을 증명.
- (b) 두 층에 대한 **정확한 항등식**: 잔여율 배율 = 1 + φ·√(c₁c₂/((1−c₁)(1−c₂))). 청산율이 높을수록 약한 상관도 크게 증폭(예: φ=0.15, c=0.895/0.58 → 1.51배; 실측 1.5, 1.6, 1.3 재현).
- (c) 공통 난이도(베타) 모형에서 닫힌 형태 r_N = Π[(1−c)s+k]/(s+k), ρ에 대해 단조증가, 층 수 N에 대해 **기하급수가 아니라 다항식 감소** N^(−cs).

**명제 5 (최적 깊이)** — 기존: 비단봉, N≤N0, 가격비 비교정학.
- (b) 최적 깊이는 용량 수준의 **첫 번째 N(분기점)**에 있음 → 탐색 단순화.
- (d) 의존성을 모르면 최악 비용은 C_h·K(1)+gN로 N에 대해 증가 → **maximin 깊이는 0 또는 1**; 2층 이상은 의존성에 대한 가정에 거는 내기.
- (e) 의존성이 커지면 모든 깊이의 비용이 비감소(증명). 그러나 **최적 깊이는 단조가 아님**(표 5: 6, 6, 7, 9, 6, 10, 6) — 처음 예상과 달라 그대로 보고. 독립 가정으로 계획하면 ρ=0.1에서 33%(바닥 있으면 45%) 추가 비용.
- 새 표 5, 부록 A 증명 갱신, 초록·서론·결론·5.2절 문장 수정. 모든 진술을 수치로 검증함(항등식 1e-14, 닫힌 형태 vs 몬테카를로 200만 표본, 점근 상수, 분기점·최악 경우 성질 무작위 3,000건).

## A. 원고 오류 수정

| 구분 | 원문 | 수정 | 근거 |
|---|---|---|---|
| Language | At least expected cost, the firm | To minimise expected cost, the firm | 'At least expected cost' is a garbled phrase; the sentence introduces the firm's objective. |
| Numbers | each call takes about 1.8 to 1.9 s on our CPU | each call takes about 1.7 to 1.8 s on our CPU | Table 5 reports L3 mean latency of 1,728-1,792 ms (capped at 2 s), i.e. 1.7 to 1.8 s. |
| Numbers | leads to 50 to 60 system failures per day | leads to 49 to 60 system failures per day | Table 7 gives 60.0, 50.0 and 49.3 failures per day. |
| Language | are the same (3 incident per day) | are the same (3 incidents per day) | Number agreement. |
| Numbers | (at about 14, 5 and 376 tickets per day) | (at about 13, 5 and 350 tickets per day) | Table 8 reports 13.1, 5.3 and 350.2 tickets per work day. |
| Numbers | one incident in 11 to 18 followed | one incident in 11 to 20 followed | Branching ratios of 0.05 to 0.09 (Table C2) imply 1/0.09 = 11 to 1/0.05 = 20. |
| Numbers | (26 to 96% across five definitions | (26 to 97% across five definitions | Table C3 gives 25.6% to 96.5% of failures. |
| Language | 23 to 28% to 30 to 32% of days without guardrails | 23 to 32% of days without guardrails | Garbled range; the abstract and Section 5.3 give 23 to 28% (c = 0.3) and 30 to 32% (c = 0.44), i.e. 23 to 32% overall. |
| Tables | Table E3 note | added tie-breaking note | Recomputation shows ties: θ = 1 (N = 3 and 4) and θ = 2 (N = 4 and 6) at k_min = 0; the table silently reports the smaller N. |

## B. AOR 투고용 변경

| 항목 | 변경 | 사유 |
|---|---|---|
| "Manuscript for double-blind review" | removed | Not verified whether Annals of Operations Research is single- or double-blind (the public guidelines pages could not be read); author information is kept on a separate title page in either case. |
| design-science / exaptation paragraph (Hevner; Gregor and Hevner) | reframed as OR contribution (stochastic inventory and capacity planning) | IS design-science positioning is specific to MIS Quarterly; AOR readers expect the OR lineage and contribution. |
| References: Gregor and Hevner (2013); Hevner et al. (2004) | removed | No longer cited after the reframing. |
| Appendix D: anonymised repository | public repository placeholder | Single-blind review needs no anonymisation; Springer asks for a data/code availability link. |
| In-text citations "(Arrow et al. 1951)" | "(Arrow et al., 1951)" | Springer author-year style puts a comma before the year in parenthetical citations. |
| Reference list (MISQ style) | Springer author-year: "Arrow KJ, Harris T, Marschak J (1951) Optimal inventory policy. Econometrica 19(3):250-272" | Reformatted automatically; entries that did not match the pattern were left unchanged (please skim once). |
| Statements and Declarations (new section) | added with [placeholders] | Springer/AOR requires funding, competing-interest, data/code availability statements; fill in the bracketed items. |

## C. 아직 남은 과제 (원고에서 해결되지 않음)

- 실증 약점: 도착 시점이 시뮬레이션이고 모델 3개·SQuAD 300문항뿐. 실제 운영 로그나 더 큰 모델·다른 과제 검증이 가장 큰 보강점.
- L2 검증기를 결과를 본 뒤 교체했으므로 사전 등록한 설정과 별도 홀드아웃에서 재실행 필요.
- OR 문헌은 추가했으나, 각 논문의 주장 요약은 제목·초록 수준으로만 썼으므로 본문을 읽고 서술 정확도를 한 번 확인할 것. human-in-the-loop 쪽 OR 문헌은 서지 확인이 안 돼 넣지 않음.

## D. 직접 채울 부분

- 저자·소속·교신저자 e-mail, Funding/Competing interests/Author contributions, 저장소 URL ([대괄호] 표시).
- PDF에서 복원한 문서라 수식 첨자(k_min, λ_N 등)는 평문. 제출 전 Word에서 서식 확인.
- 참고문헌은 Springer author-year로 자동 변환했으므로 한 번 훑어볼 것.