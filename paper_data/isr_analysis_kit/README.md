# ISR 버전 추가 분석 키트

두 가지 새 분석을 수행합니다.

- **A. 누적 변경사항을 상태로 본 hazard 분석:** 마지막 정규 릴리스 이후 merge된 PR의 누적량("작업 나이")과 달력상 경과 시간("달력 나이")을 함께 넣어 어느 쪽이 릴리스를 예측하는지 비교합니다. 작업 나이만 유의하면 변경사항 기반 상태의존, 달력 나이만 유의하면 Taylor식 cadence입니다.
- **B. upstream 모델 출시 event study:** 주요 모델 출시(events.csv)를 외생적 상태 충격으로 보고, 그 모델에 노출된 레포와 노출되지 않은 레포의 릴리스 확률을 비교합니다(stacked event study, 레포×사건 및 주×사건 고정효과, wild cluster bootstrap).
- **C. 릴리스 노트 언급 분석:** 출시 후 8주 안에 새 모델을 언급하는 릴리스가 나왔는지, 출시 후 며칠 만에 나왔는지 집계합니다.

## 실행 방법 (명령어 세 줄)

```bash
pip install requests pandas numpy scipy
export GITHUB_TOKEN=ghp_여기에_토큰        # GitHub > Settings > Developer settings > Personal access tokens
python collect.py && python analyze.py
```

- 수집은 레포 크기에 따라 몇 시간 걸릴 수 있습니다(vLLM, Transformers의 PR과 이슈가 많음). 중간에 끊겨도 다시 실행하면 이어서 진행합니다.
- 결과는 `results/results.md`에 정리되고, 세부 표는 `results/` 폴더의 CSV로 저장됩니다.
- 기존 원고와 기간을 맞추려면 `python analyze.py --end-week 2026-09-28`처럼 마지막 주(월요일 날짜)를 지정하세요.

**`results/` 폴더(또는 `results.md` 하나)를 대화에 올려주시면 원고에 반영하겠습니다.**

## 직접 확인하면 좋은 것

1. **events.csv:** 사건 날짜는 공개 발표일 기준입니다. 빠진 주요 출시나 API 변경(deprecation 등)이 있으면 같은 형식으로 행을 추가하면 됩니다. `type`은 open_weights, api_openai, api_anthropic, api_google 중 하나입니다.
2. **repo_relevance.csv:** 각 레포가 어떤 종류의 출시에 노출되는지(1) 아닌지(0)를 제가 판단해 채웠습니다. 이 표가 처치군과 대조군을 정하므로, 레포 성격을 아시는 분이 한 번 검토해 주세요.
3. **버그 분류:** 원고의 규칙(라벨에 bug 포함 또는 제목 키워드)을 그대로 구현했습니다. 원래 코드와 결과가 조금 다르면 원래 코드를 기준으로 하세요.
4. **hot-fix 분류:** 원고 규칙(패치 버전만 증가 + 7일 이내)을 쓰되, 같은 태그 접두어끼리 비교합니다. semantic-kernel처럼 python-1.2.3과 dotnet-1.2.3을 한 레포에서 내는 경우를 구분하기 위해서입니다. 7일 조건 없이 버전만으로 분류한 결과도 함께 출력합니다(원고의 순환성 문제 대응).
