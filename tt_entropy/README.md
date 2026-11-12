# 1단계 실험: 얽힘 엔트로피가 사용자별 필요 용량을 예측하는가 (H1)

연구 제안서 "Entanglement-Guided Capacity Allocation for Mass-Personalized LLMs"의 1단계 코드입니다.

브랜드(사용자) 하나마다 다음을 합니다.

1. 어댑터 없는 기본 모델의 검증 손실(응답 토큰 NLL)을 잽니다.
2. **probe:** 고정된 bond dimension(기본 8)으로 짧게 미세조정한 뒤, 각 층의 업데이트 ΔW에서 bond별 얽힘 엔트로피를 계산합니다.
3. **sweep:** bond dimension을 1, 2, 4, 8, 16으로 바꿔 가며 미세조정하고 검증 손실을 잽니다.
4. **필요 용량(capacity need):** 최대 개선폭의 90%에 처음 도달하는 가장 작은 bond dimension입니다.

마지막으로 `analyze.py`가 probe 엔트로피와 필요 용량의 순위 상관(Spearman)을 계산합니다. 상관이 높으면 H1을 지지합니다.

| 파일 | 내용 |
| --- | --- |
| `tt.py` | TT(MPO) 어댑터, 층 교체, bond별 얽힘 엔트로피 계산 |
| `data.py` | TWCS(트위터 고객지원) 변환기, JSONL 로더, 테스트용 합성 사용자 |
| `phase1.py` | 사용자별 probe와 sweep 실행. 사용자마다 JSON 하나를 저장하고, 다시 실행하면 끝난 사용자는 건너뜀 |
| `analyze.py` | H1 상관 분석 표, 요약 JSON, 산점도 |
| `test_tt.py` | TT 수축과 엔트로피 계산 검증 |

## 1. 설치 (WSL2 Ubuntu)

Windows 디스크(`/mnt/c/...`)는 WSL에서 느리므로 리눅스 홈 폴더에서 작업하세요.

```bash
cd ~
git clone -b claude/admiring-mccarthy-05nfr1 https://github.com/ooklee-sudo/fluffy-meme.git
cd fluffy-meme/tt_entropy
source ~/qtn/bin/activate
pip install -r requirements.txt
```

저장소가 비공개라면 clone할 때 GitHub 로그인(개인 액세스 토큰)이 필요합니다.

## 2. 동작 확인 (다운로드 없음, 1분 이내)

```bash
python test_tt.py
python phase1.py --tiny
python analyze.py results/phase1_tiny
```

`--tiny`는 무작위 초소형 모델과 합성 데이터로 코드 흐름만 확인합니다. 이 결과의 숫자에는 의미가 없습니다.

## 3. 데이터 준비: Customer Support on Twitter

1. Kaggle에서 "Customer Support on Twitter" 데이터셋(`thoughtvector/customer-support-on-twitter`)을 내려받습니다. Kaggle 로그인이 필요하고, **이용 조건을 먼저 확인하세요.**
2. 압축을 풀어 `twcs.csv`를 WSL로 복사합니다. 예를 들어 Windows의 다운로드 폴더에 풀었다면:

```bash
mkdir -p data
cp /mnt/c/Users/<Windows사용자>/Downloads/twcs/twcs.csv data/
```

3. 브랜드별 (고객 트윗, 브랜드 답글) 쌍으로 변환합니다. 답글이 200개 이상인 브랜드만 남깁니다.

```bash
python data.py twcs data/twcs.csv data/twcs_pairs.jsonl 200
```

## 4. 실행 (RTX 5070 Laptop 8GB 기준 기본값)

기본 설정은 Qwen2.5-1.5B(bf16, gradient checkpointing), 문장 길이 256, 배치 4, 답글이 가장 많은 브랜드 10개입니다. 모델은 처음 실행할 때 Hugging Face에서 자동으로 내려받습니다(약 3GB).

먼저 브랜드 1개로 시간을 재 보세요.

```bash
python phase1.py --n-tenants 1
```

괜찮으면 10개 전체를 돌립니다. 중간에 끊겨도 다시 실행하면 끝난 브랜드는 건너뜁니다.

```bash
python phase1.py --n-tenants 10
python analyze.py
```

브랜드는 기본적으로 답글 수 순위 전체에서 고르게 뽑습니다(`--select spread`). 가장 큰 브랜드만 쓰려면 `--select largest`, 특정 브랜드만 쓰려면 `--tenants AppleSupport,Delta`를 주세요.

결과는 `results/phase1/<브랜드>.json`, `results/phase1_summary.json`, `results/phase1_h1.png`에 저장됩니다.

**메모리가 부족하면(CUDA out of memory):** `--bs 2`, `--max-len 192`, 또는 `--model Qwen/Qwen2.5-0.5B` 순서로 줄이세요.

**빠르게 훑어보기:** `--steps 150 --ranks 1,4,16`

## 주요 옵션

| 옵션 | 기본값 | 의미 |
| --- | --- | --- |
| `--model` | `Qwen/Qwen2.5-1.5B` | 기본 모델 |
| `--targets` | `q_proj,v_proj` | 어댑터를 붙일 층 |
| `--d` | 4 | 어댑터당 TT 코어 수 |
| `--probe-rank`, `--probe-steps` | 8, 60 | probe의 bond dimension과 학습 step |
| `--ranks`, `--steps` | `1,2,4,8,16`, 300 | sweep할 bond dimension과 run당 step |
| `--frac` | 0.9 | 필요 용량 기준 (최대 개선폭 대비 비율) |
| `--n-train`, `--n-eval` | 320, 80 | 브랜드당 학습·검증 쌍 수 |

## 알아둘 점

- probe의 엔트로피는 bond마다 log(probe rank) 이하로 제한됩니다. 그래서 정규화 엔트로피(`mean_norm_entropy`)를 주 지표로 씁니다. probe rank를 바꿔 결과가 유지되는지 확인하는 것도 강건성 점검이 됩니다.
- 필요 용량은 bond dimension 몇 단계 중 하나라서 동점이 많습니다. 브랜드 10개로 얻은 p값은 첫 신호로만 보세요. 본 실험에서는 브랜드 수와 반복(seed)을 늘립니다.
- ΔW는 매 forward마다 코어에서 전체 행렬로 계산합니다. 1~2B 모델에서는 문제없지만 서빙 효율 측정(H3)용 구현은 아닙니다.
