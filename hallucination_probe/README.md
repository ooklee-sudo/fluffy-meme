# 소형 LLM 환각 탐지 연구 — 1주차 코드

LLM이 질문에 답할 때 **답이 틀릴지(환각)를 모델 내부 표현만 보고 예측할 수 있는지** 연구하기 위한 코드입니다.
RTX 5070 노트북(VRAM 8GB) 기준으로 작성했습니다.

| 파일 | 하는 일 |
| --- | --- |
| `generate.py` | 8B 모델을 4bit로 불러와 질문에 답하고, 정답 여부와 확신도 점수, **모든 층의 hidden state**를 저장 |
| `quick_check.py` | 정확도, 확신도 기반 탐지 성능(AUROC), 층별 probe 성능을 계산하고 그래프로 저장 |
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

## 다음 단계

이 코드는 답변 생성, 정답 라벨, 층별 hidden state 저장까지 하는 **공통 기반**입니다.
2주차부터는 연구 주제에 맞춰 분석 스크립트를 추가합니다.
