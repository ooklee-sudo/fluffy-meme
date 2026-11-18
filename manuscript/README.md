# 원고 조립과 남은 일

## 구조
- 섹션 파일: `00_front.md`(제목·초록) → `01_introduction.md` → `02_literature.md` → `03_model.md` → `04_analysis.md` → `05_evidence.md` → `06_discussion.md`(6절, 7절) → `07_references.md` → `A_appendix.md`(증명, 실험 세부).
- `python3 -I sim/build_manuscript.py`가 표(`sim/section5_tables.py`가 분석 결과 JSON에서 생성)와 그림(`figures/`)을 채워 `manuscript/manuscript_draft.md`를 만들고, 일관성 검사를 돌린 뒤 pandoc으로 `manuscript_draft.docx`를 만든다.
- 그림 생성: `python sim/make_figures.py` (numpy, matplotlib). 표 입력 JSON: `sim/table4_two_component.py`, `sim/free_crosscheck_analysis.py`, `sim/free_transfer_decomposition.py`.
- 이전 초안 파일(`msom_draft_*.md`)은 상태 메모와 주장 대장을 위해 남겼고 더 이상 원고의 원본이 아니다.

## 자동 검사가 확인하는 것
미해결 자리표시자, 옛 문자열(0.39, ISR 등), 핵심 숫자 (80,036; 11,352; 0.40; 0.74), 그림 1–4와 표 1–6의 캡션과 본문 참조, 명제 1–4, 한글·상태 태그 잔존, 본문 인용의 참고문헌 존재(단순 규칙이라 완전하지 않음).

## 아직 확인되지 않은 것 (투고 전에 해결)
1. **참고문헌**: Alves et al.(DeCCaF)의 저자와 게재처, Allen–Cunneen 근사의 원출처. Milgrom–Shannon, Topkis, Lee–Cohen의 서지는 기억과 검색 결과에 근거하므로 대조할 것.
2. ~~보조정리 A1(자기 인계 포함)~~ **검증 완료** (`sim/chain_selftransfer.py`, `sim/check_proofs_selftransfer.py`): 무작위 40개 파라미터에서 a_c, z_c, P_c의 단조성, 임계의 H·d에 대한 단조성(동률 1e-9 허용), 검증 가치의 단조성·포화·포락선 항등식 위반 0건. 명제 3(d)(자기 인계에 대한 단조성)는 결합 논증으로 증명.
3. ~~그림 1–3의 파라미터~~ **달러 보정으로 갱신 완료**: 그림 1은 F=$12.35/22/44, 그림 2는 θ_h=0과 0.5 두 패널(자기 인계가 검증의 가치를 낮춰 검증 채택 칸이 줄어듦), 그림 3은 오류가 잦은 DeepSeek 유형(최대 손실 7~17%, 오류가 드문 Sonnet 유형에서는 0.1% 미만). 숫자는 `figures/figure_numbers.json`에서 원고와 캡션에 자동으로 채워진다.
4. ~~비용 파라미터~~ **달러로 보정함** (`sim/calibration.py`, 원고 부록 C). 사람 인계 $8.82(범위 $6–13.5), 오답 수리 $12.35(재문의 1회), 단계 비용·완료 확률·오류율은 우리 로그에서 측정. **남은 문제**: (i) 출처가 벤더·2차 자료라 SQM, ICMI, Gartner 원문 확인이 필요하고, (ii) 오답 비용 F는 도메인마다 다르며 $22와 $44는 근거 없는 가정이고, (iii) 지연 비용 ω는 BLS 중위 임금을 고객 시간 가치로 쓴 가정이다. **도메인별 F 근거(부록 C 표 C3, `sim/f_domains.py`)**: 소매 $29–157(반품 처리 $10–30 + 차지백), 항공 $8.8–609(Moffatt v. Air Canada CA$812, EU261 €250–600; 중대 사례 비율은 관측 불가라 가정), 코딩은 개발자 임금 $65/시간(시간 수는 가정). 소매 반품·차지백 비용의 1차 출처는 확인하지 못했다(벤더 자료). 도메인별 θ도 따로 추정했다(표 7): 효과는 소매에 집중되고 항공(50과제)은 구간이 넓어 검출 불가. 보정 결과 임계는 F/H 비율에 거의 전적으로 좌우된다 (F가 인계의 약 1.4배이면 횟수 규칙이 거의 작동하지 않고, 2.1배 이상이어야 5회 이내).
5. **경쟁 논문**: Wang & Rachev, Lin & Zhang는 본문을 읽었고 나머지(Lykouris & Weng, Turan, DeCCaF)는 초록만 읽었다. 투고 중인 저널 확인.
6. **AI 사용 공개**: 이전 심사에서 AE가 AI 작성을 의심했다. 이 원고의 작성 과정에 AI가 쓰였다면 투고 저널(INFORMS/M&SOM)의 정책을 확인해 공개 요건을 따를 것. 문체를 사람이 다시 읽고 다듬는 것도 필요하다.
7. 분량(본문 약 5,500단어 + 부록)과 저널 양식 점검, 그림의 흑백 인쇄 가독성.
8. 결과의 한계는 본문 5.5, 6.3에 적어 두었다: 한 에이전트·한 도메인의 인계율 증가, 추정기 의존(DeepSeek), 탐색적 분석, 직접 조작하지 않은 검증.
