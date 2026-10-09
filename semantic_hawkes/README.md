# Semantic Hawkes

텍스트로 설명된 이벤트 타입의 LLM 임베딩에서 Hawkes 과정 파라미터(배경률 μ, 분기비 A, 감쇠 β)를 만드는 모델과, 자유 파라미터 Hawkes 기준선의 비교 코드입니다. 문헌 조사는 [LITERATURE.md](LITERATURE.md).

```bash
pip install torch numpy                 # LLM 인코더를 쓸 때만 transformers 추가
python -m semantic_hawkes.test_model    # 닫힌 형태 우도 = 수치적분 검증
python -m semantic_hawkes.train         # 데이터 효율 실험 (CPU 약 4분)
python -m semantic_hawkes.train --encoder hf:Qwen/Qwen2.5-0.5B   # LLM 임베딩 (미검증)
```

| 파일 | 내용 |
|---|---|
| `data.py` | 토픽 구조를 가진 합성 다변량 Hawkes 데이터 (Ogata thinning) |
| `encoders.py` | 이벤트 타입 설명 → 임베딩 (해시 BoW / HF 모델 평균 풀링) |
| `model.py` | `SemanticHawkes`, `FreeHawkes`, 정확한 로그우도, 다음 타입 정확도 |
| `train.py` | n_train을 바꿔가며 두 모델 비교 (test LL, 정확도, A 복원 상관) |
| `test_model.py` | 우도 정확성·기울기 검증 |

## 합성 실험 결과 (K=12, 3 시드 평균, 해시 BoW 인코더)

| n_train | 모델 | test LL/event | 다음 타입 acc | corr(Â, A) |
|---|---|---|---|---|
| 20 | free | -2.254 | 0.184 | 0.710 |
| 20 | semantic | **-2.164** | 0.145 | 0.503 |
| 50 | free | -2.137 | 0.191 | 0.866 |
| 50 | semantic | **-2.060** | 0.186 | 0.846 |
| 200 | free | -2.018 | 0.201 | 0.975 |
| 200 | semantic | **-2.015** | 0.193 | 0.960 |
| 800 | free | **-1.997** | 0.203 | 0.996 |
| 800 | semantic | -2.011 | 0.195 | 0.966 |
| oracle | 참 파라미터 | -1.994 | 0.203 | 1.0 |

해석 (과대해석 주의):
- 데이터가 적을 때(≤200 시퀀스) 텍스트 기반 모델이 우도에서 앞서지만, **n=800에서는 자유 파라미터 모델이 더 좋음**. 텍스트가 주는 것은 *사전 구조(토픽)* 뿐이라 타입별 고유 효과는 표현하지 못하고, 데이터가 충분하면 그 한계가 드러남.
- 다음 타입 정확도와 A 복원 상관에서는 모든 크기에서 우위가 없음 (n=20에서는 오히려 낮음).
- 합성 데이터이며 인코더가 해시 BoW라서, 실제 LLM 임베딩·실데이터에서의 결론은 별도 검증이 필요함.
