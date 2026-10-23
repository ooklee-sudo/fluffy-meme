# LLM 코딩 텍스트 특성 → 반응 count (Poisson/NB) 분석

리뷰/광고 텍스트의 특성을 LLM으로 코딩하고, 반응 count(helpful votes 등)에 미치는 영향을 포아송·음이항 회귀로 추정하는 파이프라인.

| 파일 | 역할 |
|---|---|
| `codebook.md` | 변수 정의·앵커 예시·신뢰도 검증 프로토콜 |
| `schema.json`, `prompts.py` | JSON 스키마, 시스템 프롬프트(+민감도 변형), 응답 검증 |
| `load_data.py` | Yelp / Amazon 2023 로더, 층화 표본, 합성 데모 데이터 |
| `llm_coding.py` | Anthropic API 코더(캐시·재시도·검증), 오프라인 mock 코더 |
| `reliability.py` | 가중 κ, Krippendorff α(순서형), Spearman |
| `lexicon.py` | 사전 기반 baseline(VADER 복합점수, 느낌표, 대문자 비율, 숫자 수) — RQ2의 M1 |
| `embeddings.py` | 텍스트 임베딩 baseline: TF-IDF→SVD(오프라인 기본) 또는 sentence-transformers→PCA, 표준화된 `emb_*` 열 |
| `correction.py` | 측정오차 보정 Poisson (DSL/PPI 계열 추정방정식, 클러스터-강건 분산) |
| `tests/check_correction.py` | 보정 추정량의 편향·95% 포함률 몬테카를로 점검 |
| `models.py` | 과대산포 진단, Poisson/NB2(클러스터-강건 SE), IRR, 그룹 K-fold held-out deviance, 이질성(H3) |
| `run_pipeline.py` | 전체 실행 |
| `docs/literature_review.md` | 선행연구·이론·가설 (**인용은 투고 전 검증 필요**) |

## 실행
```bash
pip install -r requirements.txt
python run_pipeline.py --source demo --coder mock          # 오프라인 동작 확인 (연구용 아님)

export ANTHROPIC_API_KEY=...
python run_pipeline.py --source yelp --review-path yelp_academic_dataset_review.json \
  --user-path yelp_academic_dataset_user.json --n 30000 --coder anthropic
python run_pipeline.py ... --human-labels human.csv        # 인간 라벨과 신뢰도 비교 (review_id + 코딩 변수)
```
코딩 결과는 `out/coding_cache_*.jsonl`에 캐시되어 중단 후 재개 가능. 모델/프롬프트 변형은 `--model`, `--variant alt`.

## 주의
- `mock` 코더와 `demo` 데이터는 코드 검증용이며 연구 결과가 아님.
- 실제 연구 전: 인간 라벨 300–500건으로 신뢰도 확인(α/κ ≥ 0.67), 데이터 라이선스(Yelp/Amazon) 확인, 비용 추정을 위해 소표본 먼저 실행.
- **측정오차 보정(`correction.py`)**: 인간 라벨이 분석 행의 **단순 무작위 표본**일 때만 유효(편의표본 불가; 층화표본은 행별 `pi` 필요). 보정 대상은 *인간이 코딩한 회귀*의 계수이며 LLM 코드는 분산을 줄이는 역할. 설명변수가 많고 희소 범주(예: `dominant_emotion`)가 있으면 라벨 수백 건으로는 신뢰구간이 넓으므로 라벨 수를 늘리거나 사양을 줄일 것.
- 합성 데모 점검(`python tests/check_correction.py`): 단순 LLM 회귀는 감정강도 계수에서 약 -0.018의 감쇠 편향, 보정 추정량은 편향 ≈ 0, 95% 포함률 0.95–1.00. 모의 오류 구조에 대한 결과일 뿐 실제 LLM 오류에 대한 보증은 아님.
- RQ2: M0 통제 / M1 +VADER / M2 +LLM / M3 +VADER+LLM을 그룹 K-fold held-out deviance로 비교에 더해 M4 +임베딩 / M5 +임베딩+LLM (`--embedding tfidf|st|none`, `--emb-dim 20`). 차원축소는 비지도이며 전체 텍스트로 적합(결과변수 정보 누출 없음, transductive). `st` 백엔드는 가중치 다운로드가 필요해 이 환경에서는 실행해 보지 못함.
