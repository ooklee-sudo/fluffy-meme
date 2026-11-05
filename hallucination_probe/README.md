# 환각 탐지기(probe)는 모델 업데이트 후에도 쓸 수 있는가?

LLM의 hidden state로 **답이 틀릴지(환각)를 예측하는 탐지기(probe)** 를 만들고,
모델이 업데이트(Base → Instruct, LoRA 파인튜닝)된 뒤에도 그 탐지기가 통하는지,
**정답 라벨 없이** 새 모델에 맞게 보정할 수 있는지 연구하는 코드입니다.
RTX 5070 노트북(VRAM 8GB) 기준으로 작성했습니다.

| 파일 | 하는 일 |
| --- | --- |
| `generate.py` | 8B 모델을 4bit로 불러와 질문에 답하고, 정답 여부와 확신도 점수, **모든 층의 hidden state**를 저장 |
| `quick_check.py` | 정확도, 확신도 기반 탐지 성능(AUROC), 층별 probe 성능을 계산하고 그래프로 저장 |
| `transfer.py` | 이전 모델의 probe를 새 모델에 옮겼을 때 성능 비교(그대로 / 라벨 없이 보정 / 새로 학습) |
| `finetune_lora.py` | 모델 업데이트를 만들기 위한 LoRA(QLoRA) 파인튜닝 |
| `common.py` | 데이터·모델 로딩, 프롬프트, 채점 함수 |

## 1. 환경 설정

Windows라면 **WSL2(Ubuntu)** 를 권장합니다. bitsandbytes 같은 라이브러리가 더 잘 동작합니다.

```bash
python -m venv .venv && source .venv/bin/activate
# RTX 50 시리즈는 CUDA 12.8 이상 PyTorch 빌드가 필요합니다
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

설치 확인:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

> 실험할 때는 노트북 **전원을 연결하고 고성능 모드**로 두세요. 배터리 모드에서는 GPU 전력이 제한되어 매우 느려집니다.

## 2. 실행

### (1) 먼저 작은 규모로 동작 확인 (약 5분)

```bash
python generate.py --model Qwen/Qwen3-1.7B --quant none --n 50 --out runs/test
python quick_check.py runs/test
```

### (2) 본 실험: 8B 모델, TriviaQA 1,000문항

```bash
python generate.py --model Qwen/Qwen3-8B --dataset triviaqa --n 1000 --out runs/qwen3-8b_triviaqa
python quick_check.py runs/qwen3-8b_triviaqa
```

- 중간에 멈춰도 같은 명령을 다시 실행하면 **이어서 진행**합니다.
- 다른 데이터셋: `--dataset nq` (Natural Questions)
- 직접 만든 질문 세트: `--dataset jsonl --data-path 파일.jsonl` (한 줄에 `{"question": ..., "answers": [...]}`)
- Llama 모델(`meta-llama/Llama-3.1-8B-Instruct`)은 Hugging Face에서 사용 승인을 받은 뒤 `huggingface-cli login`이 필요합니다.

## 3. 결과물 (`runs/<이름>/`)

| 파일 | 내용 |
| --- | --- |
| `generations.jsonl` | 문항별 질문, 정답 목록, 모델 답변, 정답 여부(`correct`), 확신도 점수 |
| `hidden_prompt.npy` | 답하기 **직전**(프롬프트 마지막 토큰)의 층별 hidden state, `(N, 층수+1, hidden)` float16 |
| `hidden_answer.npy` | 답변 **마지막 토큰**의 층별 hidden state |
| `quick_check.json`, `probe_auroc.png` | 정확도, 기준선 AUROC, 층별 probe AUROC |

용량: Qwen3-8B 1,000문항 기준 hidden state 파일 두 개 합계 약 0.6GB.

## 4. 결과 읽는 법

- **AUROC**: 0.5면 찍는 수준, 1.0이면 맞는 답과 틀린 답을 완벽히 구별.
- `mean_logprob` 등 **기준선**은 모델 출력 확률만 쓴 탐지 성능입니다.
- **probe 곡선이 기준선보다 높으면** "모델 내부에는 출력 확률보다 더 많은 '모른다'는 신호가 있다"는 근거가 됩니다. 보통 중간층에서 가장 높게 나옵니다.
- `prompt` 위치에서도 성능이 나오면 **답을 생성하기 전에** 환각을 예측할 수 있다는 뜻이라 특히 의미 있는 결과입니다.

## 5. 채점 방식 주의

정답 판정은 "정답 별칭 중 하나가 모델 답변 안에 들어 있는가"로 자동 처리합니다(`common.grade`).
빠르지만 틀릴 수 있으니 `generations.jsonl`에서 50개 정도를 직접 확인해 오류율을 기록해 두세요. 2주차에 LLM 채점으로 보완할 예정입니다.

## 6. 2주차: probe 이전(transfer) 실험

### 실험 설정
같은 질문 2,000개를 업데이트 전(source)과 후(target) 모델에 각각 돌립니다.
두 모델이 똑같은 입력을 보도록 **`--prompt fewshot`** 을 씁니다.
질문은 세 부분으로 나눕니다.

| 부분 | 비율 | 용도 |
| --- | --- | --- |
| calib | 25% | 두 모델의 hidden state만 사용, **라벨 없음** (보정용) |
| train | 50% | source 라벨로 원래 probe 학습, target 라벨로 비교용 probe 학습 |
| test | 25% | target 모델 답의 정답 여부를 맞히는 AUROC로 평가 |

### 비교하는 방법

| 방법 | 새 모델 라벨 필요? | 설명 |
| --- | --- | --- |
| naive | 아니오 | 이전 probe를 그대로 사용 |
| restandardize | 아니오 | 새 모델 hidden state의 평균·분산만 다시 맞춤 |
| **linear map** | 아니오 | 새 모델 hidden state → 이전 모델 hidden state 선형 대응(ridge)을 calib에서 학습한 뒤 이전 probe 적용 |
| target k labels | k개 | 새 모델에서 라벨 k개로 새로 학습 (라벨링 비용 곡선) |
| target oracle | 전부 | 새 모델에서 라벨 전부로 새로 학습 (상한선) |
| logprob | 아니오 | probe 없이 출력 확률만 사용 (기준선) |

회복률 **R = (방법 − naive) / (oracle − naive)**: 라벨 없이 성능 차이를 얼마나 메웠는지를 뜻합니다(상위 폴더 어댑터 연구와 같은 정의).

### 실행 (노트북 GPU)

**실험 A — Base → Instruct (1.7B, 양자화 없이)**
```bash
python generate.py --model Qwen/Qwen3-1.7B-Base --quant none --prompt fewshot --n 2000 --out runs/q17b-base_fs
python generate.py --model Qwen/Qwen3-1.7B      --quant none --prompt fewshot --n 2000 --out runs/q17b_fs
python transfer.py runs/q17b-base_fs runs/q17b_fs --out results/q17b_base_to_instruct
```

**실험 B — Base → Instruct (4B, 4bit)**
```bash
python generate.py --model Qwen/Qwen3-4B-Base --prompt fewshot --n 2000 --out runs/q4b-base_fs
python generate.py --model Qwen/Qwen3-4B      --prompt fewshot --n 2000 --out runs/q4b_fs
python transfer.py runs/q4b-base_fs runs/q4b_fs --out results/q4b_base_to_instruct
```

**실험 C — LoRA 파인튜닝 전 → 후 (다른 작업인 GSM8K 수학으로 파인튜닝)**
```bash
python finetune_lora.py --model Qwen/Qwen3-4B --out adapters/q4b_gsm8k
python generate.py --model Qwen/Qwen3-4B --adapter adapters/q4b_gsm8k --prompt fewshot --n 2000 --out runs/q4b_gsm8k_fs
python transfer.py runs/q4b_fs runs/q4b_gsm8k_fs --out results/q4b_lora_gsm8k
```

결과: `results/<이름>/transfer.json`, `transfer.png`(층별 AUROC 그래프).
처음 실행할 때 문항당 시간이 출력되니, 그걸 보고 `--n`을 조절하세요.

### 결과를 해석할 때 주의할 점
작은 모델(Qwen3-0.6B, 280문항)로 동작 확인을 했을 때 다음이 보였습니다. 본 실험에서도 반드시 확인하세요.

1. **두 모델의 정답 여부가 87% 일치했습니다.** 업데이트 전후 모델이 같은 질문을 어려워하면, probe가 "모델의 내부 상태"가 아니라 "질문 난이도"만 학습해도 잘 옮겨집니다. `naive vs source labels` 항목과 비교해 이 효과를 분리해서 보고해야 합니다.
2. **출력 확률(logprob) 기준선이 probe보다 높았습니다(0.84).** probe가 logprob보다 낫지 않으면 기여가 약해지므로, 큰 모델·많은 문항에서 이 차이를 꼭 보고하세요. probe와 logprob를 함께 쓰는 방법도 대안입니다.
3. 문항이 적으면 oracle이 오히려 naive보다 낮게 나옵니다(라벨이 적어서). 이 경우 R은 계산하지 않습니다. 본 실험은 2,000문항 이상을 권장합니다.

## 다음 단계
- 다른 모델 계열(Llama-3.2-3B, Gemma-3-4B: Hugging Face 사용 승인 필요)로 실험 A를 반복
- 파인튜닝 강도(학습 step 수)에 따라 probe 성능이 얼마나 떨어지는지 곡선 그리기
- 데이터셋을 바꿔서(TriviaQA → NQ) 업데이트와 도메인 이동을 함께 보는 실험
