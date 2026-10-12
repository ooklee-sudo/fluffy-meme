# 실행 방법 (Windows)

1. 이 폴더(`isr_analysis_kit`)를 `C:\Users\leeook\isr_analysis_kit`처럼 원하는 위치에 풉니다.
2. 명령 프롬프트를 열고 폴더로 이동합니다.
   ```
   cd C:\Users\leeook\isr_analysis_kit
   ```
3. GitHub 토큰을 같은 창에서 설정합니다. 스코프를 하나도 선택하지 않은 토큰이면 됩니다.
   ```
   set GITHUB_TOKEN=ghp_여기에토큰
   ```
4. 실행합니다.
   ```
   run_windows.bat
   ```
   - 수집(`collect.py`)은 몇 시간 걸릴 수 있습니다. 중간에 끊겨도 같은 명령을 다시 실행하면 이어서 합니다.
   - PC가 절전 모드로 들어가지 않게 해 주세요.
5. 끝나면 `results` 폴더(또는 `results\results.md` 하나)를 채팅에 올려 주세요.

실행 전에 `events.csv`(출시 날짜)와 `repo_relevance.csv`(각 레포가 어떤 출시에 노출되는지)를 한 번 검토해 주세요. 처치군과 대조군이 이 표로 정해집니다.

## 원본 키트에서 바꾼 것
- Windows 한국어 환경에서 결과 파일 저장과 화면 출력이 깨지지 않도록 UTF-8을 지정했습니다.
- `run_windows.bat`을 추가했습니다(패키지 설치, 수집, 분석을 한 번에 실행, 분석 종료 주는 2026-10-05).
- 가짜 데이터(19개 레포)로 끝까지 실행되는 것을 확인했습니다. 실제 데이터에서의 결과는 아직 없습니다.
