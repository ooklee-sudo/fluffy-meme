# 논문 원고 (LaTeX)

## 만드는 순서
1. `sycophancy` 폴더에서 표와 그림을 만듭니다 (결과 파일이 있는 노트북에서).
   ```
   python make_figures.py
   ```
   → `paper/tables/`, `paper/figures/`, `paper/numbers.json`이 생깁니다.
2. `paper` 폴더 전체를 zip으로 묶어 Overleaf에 올립니다 (New Project → Upload Project).
3. Overleaf에서 컴파일합니다 (pdfLaTeX, 참고문헌 BibTeX).

## 빨간 글씨 (`\tbd{...}`)
본문에서 빨간색으로 보이는 숫자와 문장은 확인이 필요합니다. `numbers.json`과 `tables/main.md`의 값으로 바꾸고 `\tbd{}`를 지우세요.

## 참고문헌
`refs.bib`의 arXiv 항목은 모두 arXiv API로 제목과 저자를 확인했습니다 (2026-11-08). 새 참고문헌을 추가할 때도 arXiv 페이지에서 확인하세요.

## arXiv 버전 / 익명 투고 버전 전환
`main.tex` 맨 위의 한 줄만 바꾸면 됩니다.
- `\anonymousfalse` (기본): arXiv용. 저자 이름, 소속, 이메일, Zenodo DOI 포함
- `\anonymoustrue`: 이중맹검 투고용. "Anonymous Authors", 코드는 보조 자료로 표시, PDF 속성 저자도 Anonymous

익명 버전에서는 Zenodo DOI가 빠집니다 (Zenodo 기록에 저자 이름이 공개되기 때문). 투고 시스템에는 `release/room-to-reconsider-code.zip`을 보조 자료로 올리세요.

## 저널 양식
지금은 arXiv용 일반 양식(article)입니다. ACM TIST에 낼 때는 ACM 양식(`acmart`, `acmsmall`)으로 옮기면 됩니다.
