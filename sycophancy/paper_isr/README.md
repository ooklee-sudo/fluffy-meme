# ISR 원고용 LaTeX 조각

| 파일 | 내용 |
| --- | --- |
| `strategic_appendix.tex` | 전략적 사용자 모형의 증명 (가정 A1–A3, 보조정리 3개, 명제 1–6, 근거 요구 구간 따름정리) |
| `strategic_proofs.tex` | 위 부록만 따로 컴파일하는 파일 (`pdflatex strategic_proofs.tex`, 두 번 실행) |
| `strategic_proofs.pdf` | 컴파일 결과 (4쪽) |
| `research_plan_with_proofs.docx` | 연구 계획 본문(문서 내용) + 이 부록을 합친 Word 파일. 수식은 Word 수식 개체로 들어 있음 |

논문에 넣을 때는 `strategic_proofs.tex`의 `amsthm`, `xcolor`, `\newtheorem` 줄을 논문 서문에 복사하고, `\appendix` 다음에 `\input{strategic_appendix}`를 넣으면 됩니다.

표기: 작성자가 승인에서 얻는 이득은 β입니다. 연구 계획 문서에서는 b로 썼지만, 나쁜 신호 b와 겹쳐서 바꿨습니다.

수치 검증: `python strategic_user.py --check` (`sycophancy/` 폴더에서 실행).
