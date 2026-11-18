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
2. **보조정리 A1(자기 인계 포함)**: 논증은 같지만 수치 검증은 자기 인계가 없는 모형에서만 했다 (`sim/check_proofs.py`). 자기 인계 포함 모형으로 같은 점검을 돌릴 것.
3. **그림 3**은 θ_w=0.29의 앞선 모형 파라미터, **그림 2**는 자기 인계 없는 모형으로 계산했다. 정정된 추정과 맞춰 다시 그릴 것.
4. **비용 파라미터(k, c, H, F, h, ω, q, μ)는 모두 예시 값.** 콜센터 비용·처리시간 등 외부 근거로 고정.
5. **경쟁 논문**: Wang & Rachev, Lin & Zhang는 본문을 읽었고 나머지(Lykouris & Weng, Turan, DeCCaF)는 초록만 읽었다. 투고 중인 저널 확인.
6. **AI 사용 공개**: 이전 심사에서 AE가 AI 작성을 의심했다. 이 원고의 작성 과정에 AI가 쓰였다면 투고 저널(INFORMS/M&SOM)의 정책을 확인해 공개 요건을 따를 것. 문체를 사람이 다시 읽고 다듬는 것도 필요하다.
7. 분량(본문 약 5,500단어 + 부록)과 저널 양식 점검, 그림의 흑백 인쇄 가독성.
8. 결과의 한계는 본문 5.5, 6.3에 적어 두었다: 한 에이전트·한 도메인의 인계율 증가, 추정기 의존(DeepSeek), 탐색적 분석, 직접 조작하지 않은 검증.
