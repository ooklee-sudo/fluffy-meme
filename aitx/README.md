# aitx: RAG → 파인튜닝 전환 데이터 수집 파이프라인

논문 "The Fear of Losing"의 본 표본을 만드는 코드입니다. 무료 공개 자료만 사용합니다.

| 자료 | 무엇을 얻나 | 용도 |
|---|---|---|
| SEC EDGAR 전문 검색 | 10-K·10-Q·8-K에서 RAG, FT, 생성형 AI 언급 | 전환 시점(대체 측정), 산업 AI 추세 μ·변동성 σ |
| SEC 제출 자료·XBRL | 기업명, SIC, 2022년 총자산, 공시 일자, 10-K 사업 설명 | 제외 규칙 R1–R3, 공급기업 코딩, S의 분모 |
| Common Crawl | 채용관리시스템(Greenhouse, Lever 등)에 올라온 과거 채용공고 | 전환 시점(주 측정), 시간가변 S |

## 설치

```bash
pip install -r requirements.txt
export AITX_USER_AGENT="Hong Gildong gildong@university.ac.kr"   # SEC는 연락처 없는 요청을 막습니다
python -m unittest discover -s tests      # 오프라인 테스트 33개
```

## 실행 순서

처음에는 `edgar-verify --limit 50`처럼 작게 돌려 결과를 확인한 뒤 전체를 실행하세요. 모든 요청은 `data/cache/`에 저장되므로 중단 후 다시 실행하면 이어서 진행됩니다.

1. **`python -m aitx.cli edgar-search`**
   `keywords.py`의 검색어마다 EDGAR 전문 검색을 돌려 `data/edgar_hits.csv`를 만듭니다. 결과가 1만 건을 넘으면 월 단위로 나눠 다시 검색합니다.

2. **`python -m aitx.cli edgar-verify`**
   RAG·FT 검색에 걸린 문서를 내려받아 문맥 규칙으로 다시 판정합니다 → `data/edgar_docs.csv`.
   걸러내는 예: "RAG status"(프로젝트 신호등), "fine-tune our strategy", "LoRaWAN". 판정 근거 문장(snippet)이 함께 저장됩니다.

3. **`python -m aitx.cli firm-info`**
   기업별 SIC, 2022년 총자산, 공시 일자, 최근 10-K 사업 설명 발췌를 가져옵니다 → `firms.csv`, `filing_dates.csv`, `supplier_coding_sheet.csv`.

4. **수작업: 공급기업 코딩**
   `supplier_coding_sheet.csv`의 `item1_excerpt`를 읽고 코더 두 명이 `coder1`, `coder2`에 A/B/C/X를 적습니다. 불일치를 합의해 `supplier_final`에 확정합니다.
   A = AI·데이터 인프라 공급(제외), B = 생성형 AI 내장 소프트웨어 판매, C = 비소프트웨어 사용기업, X = SPAC.
   코더 간 일치도(Cohen's κ)를 논문에 보고하세요.

5. **채용공고 (선택이지만 권장)**
   - `python -m aitx.cli cc-guess`: 기업명으로 Greenhouse, Lever, Ashby 주소를 추측해 `ats_candidates.csv`를 만듭니다. 추측이므로 반드시 실제 채용 페이지와 대조하세요.
   - 확인한 행을 `data/ats_map.csv`(열: `cik, ats, slug`)에 옮깁니다. Workday, iCIMS, 자체 채용 사이트는 직접 추가합니다(`data/ats_map_template.csv` 참고).
   - `python -m aitx.cli cc-collect --ats-map data/ats_map.csv` → `data/postings.csv`

6. **`python -m aitx.cli build --source edgar`** (또는 `--source postings`)
   - `events_<source>.csv`: 기업별 상태(at_risk, ft_first, ft_only), 진입일, 전환일, T, 제외 사유(R1–R4)
   - `firm_month_<source>.csv`: 분석용 기업-월 패널(start, stop, event). 한 달 시차를 둔 S_share(누적 RAG 문서 ÷ 누적 전체 문서)와 산업 AI 추세·변동성(ind_mu, ind_sigma, 직전 24개월 기준)이 들어 있습니다.

## 분석 예시 (R)

```r
library(survival)
fm <- read.csv("data/firm_month_postings.csv")
# 손실회피(lam), CIO 권한(theta), 통제변수는 별도로 병합
fit <- coxph(Surv(start, stop, event) ~ scale(S_share) + scale(ind_sigma) + scale(ind_mu) +
               strata(cohort) + cluster(cik), data = fm)
```

## 알아둘 한계

- **서버 호출 점검 결과 (2026-09-28).** EDGAR 전문 검색·문서 내려받기, Common Crawl 인덱스 파일·WARC 조회를 실제 서버에 연결해 확인했습니다. EDGAR 전문 검색(efts.sec.gov)은 공식 문서가 없는 내부 API라 가끔 `500 Internal server error`를 돌려주는데, 클라이언트가 자동으로 다시 시도합니다. 응답 형식은 바뀔 수 있으니 실행 때마다 `edgar_hits.csv`의 열이 채워졌는지 확인하세요.
- **Common Crawl 인덱스 서버가 자주 끊깁니다.** index.commoncrawl.org는 일부 클라우드 망에서 연결을 끊거나 502를 돌려줍니다. 그러면 `data.commoncrawl.org`에 있는 인덱스 파일(cluster.idx, cdx-*.gz)을 범위 요청으로 직접 읽도록 자동 전환합니다. 결과는 같지만 조회 한 번에 요청이 20회가량 필요해 느립니다(`data/cache/`에 저장되므로 같은 조회는 다시 받지 않습니다).
- **Common Crawl의 날짜는 근사치입니다.** 크롤은 한두 달 간격으로 일부 페이지만 수집합니다. JSON-LD에 게시일(datePosted)이 있으면 그것을 쓰고, 없으면 처음 수집된 날짜를 씁니다. 그래서 실제 게시일보다 늦게 잡힐 수 있습니다.
- **Workday 등은 본문이 비어 있을 수 있습니다.** 자바스크립트로 그리는 채용 페이지는 본문이 거의 비어 있어서, `--min-text` 기준(기본 200자) 아래로 떨어지면 빠집니다. `postings.csv`의 `text_len`, `jsonld`로 기업별 수집 상태를 점검하세요.
- **정밀도를 직접 점검하세요.** 무작위 100개 문서의 snippet을 읽고 규칙 정밀도를 보고하는 것을 권합니다. 오탐이 보이면 `keywords.py`에 규칙을 추가하면 됩니다.
- **요청 속도를 지키세요.** SEC는 초당 10회 이하(기본 8회), Common Crawl 인덱스는 기본 초당 1회입니다. 이 값을 올리면 차단될 수 있습니다.
- **보완 자료가 필요한 변수:** 손실회피(CFO 재임 기간 영업권 손상 지연)와 CIO 권한(보고 라인)은 이 코드로 만들지 않습니다. Compustat이 없으면 XBRL의 GoodwillImpairmentLoss 태그로 대체할 수 있습니다.
