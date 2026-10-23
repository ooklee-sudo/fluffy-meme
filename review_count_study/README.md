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

## LLM 코딩 백엔드
- `--coder anthropic` (ANTHROPIC_API_KEY) / `--coder openrouter` (OPENROUTER_API_KEY 또는 자격증명 주입 프록시, 모델 예: `anthropic/claude-haiku-5.5`) / `--coder mock`.
- `--workers 12`로 동시 호출. 실패 행은 캐시에서 재사용하지 않고 다음 실행 때 다시 시도.
- OpenRouter 코더는 추론(reasoning)을 꺼서 JSON 잘림을 방지하고 `finish_reason=length`는 실패로 처리. 토큰 사용량은 `[usage]`로 출력.
- 비용 감각(Haiku 5.5, 입력 $0.1/M·출력 $0.5/M 기준): 리뷰 1건당 입력 약 1.2k·출력 약 0.16k 토큰 ≈ $0.0002 → 3만 건 ≈ $6 + 실제 리뷰 길이만큼 가산.

## 인간 코딩 워크플로 (측정오차 보정용)
1. `python tools/make_labeling_sheets.py --coded out/reviews_coded.parquet --out-dir labeling --n 400 --overlap 100` — 분석 행의 **단순 무작위 표본** 추출, 코더 A/B용 블라인드 CSV(LLM 코드·별점·반응 수 비공개) + `sample_key.csv`(추출 기록). 겹침 100건은 두 코더가 모두 코딩.
2. 코더는 `codebook.md`를 읽고 시트를 채움(첫 행 `#ALLOWED_VALUES`는 삭제해도 무방, 병합 시 무시됨).
3. `python tools/merge_human_labels.py --a coder_A.csv --b coder_B.csv --key sample_key.csv --out-dir labeling` — 값 검증, 코더 간 신뢰도(`inter_coder_reliability.csv`), 불일치 행(`adjudication.csv`) 출력, `human.csv` 생성. 불일치 행은 합의 후 `--adjudicated`로 되돌려 넣어야 표본이 무작위성을 유지.
4. `python run_pipeline.py ... --human-labels labeling/human.csv` — LLM-vs-인간 신뢰도와 DSL 보정 회귀가 함께 출력.

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
- RQ2: M0 통제 / M1 +VADER / M2 +LLM / M3 +VADER+LLM을 그룹 K-fold held-out deviance로 비교에 더해 M4 +임베딩 / M5 +임베딩+LLM (`--embedding tfidf|st|none`, `--emb-dim 20`). 차원축소는 비지도이며 전체 텍스트로 적합(결과변수 정보 누출 없음, transductive). 임베딩 모형은 L2(ridge) 정규화 버전도 비교: 임베딩 계수만 벌점, 통제변수·절편은 비벌점, 벌점 강도는 바깥 fold의 훈련셋 안에서 그룹 K-fold(inner)로 선택(`models.ridge_cv_alpha`). 선택된 강도가 격자(`ALPHA_GRID`) 끝이면 격자를 넓힐 것. `st` 백엔드는 가중치 다운로드가 필요해 이 환경에서는 실행해 보지 못함.
