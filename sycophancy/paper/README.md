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
`refs.bib`에서 `VERIFY`, `TODO` 표시된 항목은 arXiv 페이지에서 저자와 제목을 확인해 채우세요.

## 저널 양식
지금은 arXiv용 일반 양식(article)입니다. ACM TIST에 낼 때는 ACM 양식(`acmart`, `acmsmall`)으로 옮기면 됩니다.
