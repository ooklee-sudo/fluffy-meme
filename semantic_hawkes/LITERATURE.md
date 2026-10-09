# 문헌 조사: LLM × 시간적 점과정(TPP) / Hawkes 과정

조사일: 2026-10-09. 아래 수치와 설정은 각 논문의 arXiv HTML/PDF 본문에서 확인한 내용입니다.
Hawkes 과정 원전(Hawkes 1971), NHP/THP/SAHP 원논문 자체는 초록 수준만 확인했고 본문 검증은 하지 않았습니다.

## 1. 배경: 신경망 TPP와 벤치마크

- **TPP / Hawkes**: 사건 시퀀스를 조건부 강도 λ(t)로 모델링. 다변량 Hawkes는 과거 사건이 미래 강도를 올리는 자기·상호 흥분 구조.
- **신경망 TPP 계열**: RMTPP(RNN), NHP(연속시간 LSTM), SAHP·THP·AttNHP(어텐션), FullyNN, IFTPP(intensity-free), ODETPP.
- **EasyTPP** (Xue et al., ICLR 2024, [arXiv 2307.08097](https://arxiv.org/abs/2307.08097))
  - 고전 다변량 Hawkes(지수 커널) + 신경망 TPP 8종을 동일 학습 절차(Adam, 동일 early stopping)로 비교.
  - 데이터: Synthetic(단변량 Hawkes, μ=0.2, α=0.8, β=1.0), Amazon(K=16), Retweet(K=3), Taxi(K=10), Taobao(K=20), StackOverflow(K=22).
  - 과제: 적합도(log-likelihood), 다음 사건 예측(시간 RMSE, 타입 오류율; MBR 원칙), 장기 예측(OTD 거리).

## 2. LLM 기반 TPP

### TPP-LLM (Liu & Quan, [arXiv 2410.02062](https://arxiv.org/abs/2410.02062))
- **구조**: 프롬프트 + 이벤트 타입 *텍스트 설명* 토큰 + 시간 임베딩을 decoder-only LLM에 입력. 각 이벤트의 마지막 임베딩의 은닉 상태를 히스토리 벡터로 사용. 강도는 선형층 + softplus + 시간 감쇠항, 타입은 softmax, 시간은 선형 회귀.
- **시간 임베딩**: THP 방식의 sinusoidal 시간 위치 인코딩.
- **손실**: NLL(비사건 적분은 구간당 20개 Monte Carlo) + 타입 CE + 시간 MSE (β=1, 1).
- **학습**: LoRA(rank 16, α 16, dropout 0.05, Q/K/V/O), 4-bit 양자화, Adam lr 5e-4, batch 8, 최대 20 epoch.
- **백본**: TinyLlama-1.1B-Chat, Gemma-2-2B-IT (그 외 Llama-3.2 등은 ablation).
- **데이터**: StackOverflow, Chicago Crime, NYC Taxi, US Earthquake, Amazon Review. 공개 데이터에 타입 텍스트가 없어 *저자들이 직접 설명을 작성*.
- **베이스라인**: NHP, SAHP, THP, AttNHP, ODETPP (EasyTPP 경유).
- **결과**: 모든 지표에서 이기는 것은 아님. 로그우도는 AttNHP가 Crime/Taxi/Amazon에서, SAHP가 Earthquake에서 우위. 정확도·RMSE는 TPP-LLM이 다수 데이터에서 우위(예: StackOverflow ACC 44.2%).
- **한계**: 유의성 검정 없음(5회 실행·early stopping), 타입 텍스트 작성이 수작업, 미래 과제로 다른 미세조정·임베딩 전략 제시.

### Language-TPP (Kong et al., [arXiv 2502.07139](https://arxiv.org/abs/2502.07139))
- **핵심**: 시간 간격(32-bit float)을 4개의 *바이트 토큰*(`<|byte_0|>`…`<|byte_255|>` 256개 추가)으로 인코딩. 예: "0.075999237"이 기본 토크나이저로는 11토큰, 바이트 토큰으로는 4토큰.
- **백본**: Qwen2.5-0.5B (1.5B도 시험, 0.5B가 대부분 지표에서 더 좋았음).
- **3단계 학습**: ① 이벤트 시퀀스 continued pre-training(next-token CE) → ② next-event 미세조정(~5만 프롬프트-응답 쌍) → ③ LLM을 동결하고 강도 사영층만 TPP 우도로 학습(비사건 적분 MC 10개).
- **데이터**: Retweet, StackOverflow, Taobao, Taxi(텍스트 없음) + Amazon Review(텍스트 있음, 24타입). 전체를 합쳐 학습 후 각 테스트셋 평가.
- **베이스라인**: NHP, SAHP, THP, ANHP-G3.5(LAMP, GPT-3.5).
- **결과**: 저자 보고상 4개 TPP 데이터 모두에서 최고 TLL. 예: Retweet RMSE 18.1 / ACC 59.7(NHP 21.8 / 54.0). Taxi는 ACC 90.5로 NHP(91.5)보다 낮음. 설명문 생성 ROUGE-L 24.78 vs 22.60.
- **Ablation**: 바이트 토큰 → 일반 숫자열로 바꾸면 Retweet RMSE 18.1 → 21.8. Stage 1 제거 시 19.2.
- **한계(저자)**: 긴 텍스트 설명 시 컨텍스트 폭증, 매우 긴 시퀀스·다른 모달리티 확장성. 부록·본문 간 타입 수 불일치(Taobao 17 vs 20).

### TPP-TAL (Dec 2025, [arXiv 2601.00845](https://arxiv.org/abs/2601.00845))
- **핵심**: 시간·타입 임베딩을 단순 concat하지 않고 LLM에 넣기 전 정렬.
  - *Temporal Cross-Fusion (TCF)*: 이벤트 타입 토큰이 query, 시간 임베딩이 key/value인 cross-attention.
  - *Multi-Scale Temporal Bias Transformer (MTBT)*: 로그 버킷화한 이벤트 간격(기본 32 버킷)에 따른 헤드별 학습 가능한 어텐션 바이어스.
- **백본**: TinyLlama-1.1B-Chat (파라미터 동결).
- **베이스라인**: TPP-LLM 하나뿐(다른 방법은 미공개/부분 공개라고 서술).
- **결과(TPP-LLM → TPP-TAL)**: SOF LL −1.848→−0.475, ACC 0.439→0.796; NYC RMSE 0.892→0.443; US-EQ ACC 0.629→0.843; AMZ LL −1.047→−0.607.
- **한계**: 비교 대상 1개, 백본 1개, 오차 막대 없음. TCF 제거 변형이 일부 지표에서 풀 모델보다 좋음.

## 3. 선행연구 비교

| | 시간 표현 | 타입 표현 | 강도 형태 | 우도 계산 | 해석 가능한 상호작용 |
|---|---|---|---|---|---|
| NHP/THP 등 | 연속시간 상태/위치 인코딩 | 타입 ID 임베딩 | 신경망 | MC 또는 수치적분 | 없음 |
| TPP-LLM | sinusoidal | **텍스트 설명** | softplus(선형)+감쇠 | MC 20샘플 | 없음 |
| Language-TPP | **바이트 토큰** | 텍스트 | 은닉상태 사영+softplus | MC 10샘플 | 없음 |
| TPP-TAL | TCF + 시간 바이어스 | 텍스트 | TPP-LLM 계열 | MC | 없음 |
| **본 제안(Semantic Hawkes)** | 지수 커널 | 텍스트 임베딩(캐시) | **Hawkes 구조** | **닫힌 형태(정확)** | **A[i,k] 분기비** |

## 4. 확인된 공백과 제안의 위치

1. 위 LLM-TPP들은 모두 강도를 은닉상태에서 직접 예측하며, **사건 간 흥분 관계(Hawkes 커널)를 명시적으로 노출하지 않음**. (조사한 3편 기준.)
2. 우도 비사건 항을 **Monte Carlo로 근사**함. 지수 커널 Hawkes면 정확한 닫힌 형태가 가능.
3. 보정(calibration)·희귀 사건·해석성 평가가 조사한 논문에서는 보이지 않음.
4. 통계적 엄밀성(다중 시드, 오차 막대, 유의성)이 약함 — 재현·비교 시 주의.

## 5. 이 저장소 구현의 범위와 한계

- 합성 데이터에서의 검증이며, **위 논문들과 직접 수치 비교하지 않음**(EasyTPP 실데이터 미사용).
- 텍스트 인코더는 기본이 해시 BoW. LLM 임베딩(`--encoder hf:<모델>`)은 구현했으나 이 환경에서는 실행·검증하지 않음.
- 다음 단계: EasyTPP 실데이터(Retweet/StackOverflow/Taxi/Amazon)와 NHP·THP·TPP-LLM 대비 평가, 시간 RMSE·OTD 지표 추가, 억제 효과(음의 상호작용) 확장.
