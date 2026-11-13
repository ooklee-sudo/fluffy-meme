# 1단계 실험: 얽힘 엔트로피가 사용자별 필요 용량을 예측하는가 (H1)

연구 제안서 "Entanglement-Guided Capacity Allocation for Mass-Personalized LLMs"의 1단계 코드입니다.

브랜드(사용자) 하나마다 다음을 합니다.

1. 어댑터 없는 기본 모델의 검증 손실(응답 토큰 NLL)을 잽니다.
2. **그래디언트 probe (주 지표):** 학습 데이터 전체에 대해 고정된 원래 가중치 W의 손실 그래디언트를 누적하고, 그 행렬의 bond별 얽힘 엔트로피를 계산합니다. 학습도 초기화도 없으므로 브랜드 데이터의 구조만 반영합니다.
3. **TT probe (비교용):** 고정 bond dimension(기본 8)으로 짧게 미세조정한 뒤 ΔW의 엔트로피를 잽니다. 마지막 코어를 뺀 코어들이 무작위로 시작해서, 이 값은 초기화의 영향을 크게 받습니다. 첫 실행에서 모든 브랜드가 0.92 근처로 같게 나온 이유입니다.
4. **sweep:** bond dimension을 1, 2, 4, 8, 16으로 바꿔 가며 미세조정하고(dev 기준 조기 종료) 평가 손실을 잽니다.
5. **필요 용량(capacity need):** 최대 개선폭의 90%에 도달하는 bond dimension을 격자 사이에서 log2 기준으로 보간한 연속값입니다(`capacity_need_grid`는 격자값).

마지막으로 `analyze.py`가 신호와 필요 용량의 순위 상관(Spearman)을 계산합니다. **주 검정은 미리 정한 하나**(그래디언트 probe의 정규화 엔트로피)이고, 나머지 행은 탐색용이라 Holm 보정 p값을 같이 보여 줍니다.

이미 sweep까지 끝낸 결과에 그래디언트 probe만 추가하려면 같은 설정에 `--reprobe`를 붙여 실행합니다. sweep은 다시 돌리지 않아 브랜드당 1~2분이면 됩니다.

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
| `--ranks` | `1,2,4,8,16` | sweep할 bond dimension |
| `--frac` | 0.9 | 필요 용량 기준 (최대 개선폭 대비 비율) |
| `--n-train`, `--n-dev`, `--n-eval` | 320, 40, 80 | 브랜드당 학습, 조기 종료용, 평가용 쌍 수 (서로 겹치지 않음) |
| `--steps`, `--eval-every` | 300, 50 | run당 최대 step과 dev 평가 간격. dev 손실이 가장 낮았던 시점(0 step 포함)으로 되돌림 |
| `--lr`, `--rank-scale` | 1e-3, `rs` | 학습률과 rank 보정. `rs`는 업데이트에 1/√(bond dimension)을 곱해 큰 rank가 더 크게 움직이지 않게 함 (rsLoRA와 같은 방식) |

## 알아둘 점

- probe의 엔트로피는 bond마다 log(probe rank) 이하로 제한됩니다. 그래서 정규화 엔트로피(`mean_norm_entropy`)를 주 지표로 씁니다. probe rank를 바꿔 결과가 유지되는지 확인하는 것도 강건성 점검이 됩니다.
- 필요 용량은 bond dimension 몇 단계 중 하나라서 동점이 많습니다. 브랜드 10개로 얻은 p값은 첫 신호로만 보세요. 본 실험에서는 브랜드 수와 반복(seed)을 늘립니다.
- ΔW는 매 forward마다 코어에서 전체 행렬로 계산합니다. 1~2B 모델에서는 문제없지만 서빙 효율 측정(H3)용 구현은 아닙니다.

## 확인용 실행 (사전 등록된 H1 검정)

첫 10개 브랜드는 결과를 이미 본 탐색용입니다. 확인용 검정은 `PREREGISTRATION.md`에 가설, 표본(새 브랜드 30개), 주 검정(응답 길이를 통제한 편상관, 양측), 제외 기준을 실행 전에 고정해 두었습니다. 실행 중에 설정을 바꾸면 그 문서의 7절(Deviations)에 기록하세요.

1. 탐색용 10개에 같은 토큰 예산(4,000) probe를 다시 계산합니다 (약 5분):

```bash
python phase1.py --n-tenants 10 --reprobe && python analyze.py
```

2. 확인용 30개 브랜드 목록이 `PREREGISTRATION.md` 8절과 같은지 확인합니다:

```bash
python phase1.py --exclude-dir results/phase1 --n-tenants 30 --list-only
```

3. 확인용 실행 (seed 2개, 브랜드당 약 10분, 전체 약 5시간):

```bash
python phase1.py --exclude-dir results/phase1 --n-tenants 30 --seeds 0,1 --out results/phase1_confirm
```

4. 분석. 출력의 `PRIMARY` 줄이 사전 등록한 검정입니다:

```bash
python analyze.py results/phase1_confirm
```

## 두 번째 확인용 실행 (H1′: 엔트로피와 맞춤화 이득)

첫 확인용 검정에서 H1은 지지되지 않았습니다(`PREREGISTRATION.md` 9절). 그 뒤 탐색 분석(`python explore.py`)에서 엔트로피가 맞춤화 이득과 연결되는 신호가 보여서, 아직 쓰지 않은 브랜드 30개로 다시 검정합니다. 가설, 표본, 주 검정(상대 gain, 네 특성 통제, 양측)은 `PREREGISTRATION_H1prime.md`에 고정했습니다.

```bash
python phase1.py --exclude-dir results/phase1,results/phase1_confirm --n-tenants 30 --list-only
```

```bash
python phase1.py --exclude-dir results/phase1,results/phase1_confirm --n-tenants 30 --seeds 0,1 --out results/phase1_value
```

```bash
python analyze_value.py results/phase1_value
```

## 탐색 분석: 메커니즘과 의사결정 가치 (GPU 불필요, 사전 등록 아님)

```bash
python mechanism.py
```

신호가 어느 모듈(q, v), 어느 깊이, 어느 bond에 있는지, 그리고 MPO bond 엔트로피가 일반 SVD 엔트로피를 통제해도 효과가 남는지 봅니다.

```bash
python decision.py
```

예산 때문에 일부 브랜드만 맞춤화할 때, 엔트로피, 단순 특성, 무작위 중 어떤 규칙이 전체 이득을 가장 많이 확보하는지 봅니다. 규칙은 한 표본에서 만들고 다른 표본에서 평가합니다. probe 비용은 `--probe-cost`로 바꿀 수 있습니다(기본 0.25, 어댑터 학습 1회 = 1).

## 2단계: TT 어댑터 vs LoRA (H2, 사전 등록: `PREREGISTRATION_H2.md`)

사용자당 파라미터 예산을 맞춘 상태에서 TT 어댑터, LoRA, VeRA의 상대 gain을 비교합니다. 어댑터 구현은 `adapters.py`, 실험은 `phase2.py`입니다.

1. 학습률 조정. 탐색용 10개 브랜드로 약 1.5~2시간 걸립니다:

```bash
python phase2.py --tune --tenants-from results/phase1 --out results/phase2_tune
```

```bash
python analyze_tune.py results/phase2_tune
```

마지막에 나온 `--lrs ...` 값을 `PREREGISTRATION_H2.md` 8절에 기록하고 커밋한 뒤에 본 실험을 시작합니다. 고른 값이 격자 끝이면 안내에 따라 격자를 넓혀 다시 조정합니다.

2. 본 실험. 아직 쓰지 않은 31개 브랜드로 seed마다 약 5시간 걸립니다. 하룻밤에 seed 하나씩 돌리세요:

```bash
python phase2.py --exclude-dir results/phase1,results/phase1_confirm,results/phase1_value --n-tenants 31 --lrs <조정 결과> --seed 0 --out results/phase2_s0
```

```bash
python phase2.py --exclude-dir results/phase1,results/phase1_confirm,results/phase1_value --n-tenants 31 --lrs <조정 결과> --seed 1 --out results/phase2_s1
```

3. 분석과 지연시간 측정:

```bash
python analyze_h2.py results/phase2_s0 results/phase2_s1
```

```bash
python bench.py
```

