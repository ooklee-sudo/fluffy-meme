# 논문 원고 (LaTeX)

## 파일 구조
| 파일 | 내용 |
| --- | --- |
| `main.tex` | **arXiv 버전** (일반 article 양식) |
| `main_acm.tex` | **ACM TIST 투고 버전** (`acmsmall` 양식, CCS Concepts, 키워드) |
| `abstract.tex`, `body.tex`, `appendix.tex` | 두 버전이 **함께 쓰는** 초록, 본문, 부록. 고칠 때는 여기만 고치면 두 버전에 같이 반영됩니다 |
| `refs.bib` | 참고문헌 (arXiv API로 확인 완료) |
| `tables/`, `figures/` | `make_figures.py`가 만드는 표와 그림 |

## 만드는 순서
1. `sycophancy` 폴더에서 표와 그림을 만듭니다.
   ```
   python make_figures.py
   ```
2. `paper` 폴더 안의 내용을 zip으로 묶어 Overleaf에 올립니다 (New Project → Upload Project).
3. Overleaf 왼쪽 위 Menu에서 **Main document**를 고릅니다.
   - arXiv용: `main.tex`
   - TIST 투고용: `main_acm.tex`

## 익명 버전
두 파일 모두 맨 위의 `\anonymousfalse`를 `\anonymoustrue`로 바꾸면 저자 이름과 Zenodo DOI가 빠집니다. TIST 안내문에는 익명화 요구가 없어서 기본(이름 포함)으로 내면 됩니다. 제출 화면에서 익명 원고를 요구하면 그때 바꾸세요.

## 빨간 글씨 (`\tbd{...}`)
확인이 필요한 부분입니다. 반박 문구 실험(`q4b_sure_*`, `q4b_wrong_*`)이 끝나고 `make_figures.py`를 다시 돌리면 부록의 빨간 글씨가 표로 바뀝니다.

## arXiv 제출
LaTeX 원본을 올려야 합니다. Overleaf의 **Submit → arXiv**에서 `main.bbl`이 포함된 zip을 받으세요.

## 투고 시스템 보조 자료
`../release/room-to-reconsider-code.zip` (익명 재현 코드)
