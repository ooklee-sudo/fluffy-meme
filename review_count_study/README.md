# LLM 코딩 텍스트 특성 → 반응 count (Poisson/NB) 분석

리뷰/광고 텍스트의 특성을 LLM으로 코딩하고, 반응 count(helpful votes 등)에 미치는 영향을 포아송·음이항 회귀로 추정하는 파이프라인.

| 파일 | 역할 |
|---|---|
| `codebook.md` | 변수 정의·앵커 예시·신뢰도 검증 프로토콜 |
| `schema.json`, `prompts.py` | JSON 스키마, 시스템 프롬프트(+민감도 변형), 응답 검증 |
| `load_data.py` | Yelp / Amazon 2023 로더, 층화 표본, 합성 데모 데이터 |
| `llm_coding.py` | Anthropic API 코더(캐시·재시도·검증), 오프라인 mock 코더 |
| `reliability.py` | 가중 κ, Krippendorff α(순서형), Spearman |
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
- LLM 변수의 측정오차 보정(PPI/DSL)은 문서에 설계만 기술되어 있고 아직 코드에는 구현되지 않음.
