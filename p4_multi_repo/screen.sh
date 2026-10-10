#!/bin/bash
for r in BerriAI/litellm pydantic/pydantic-ai PrefectHQ/fastmcp modelcontextprotocol/python-sdk marimo-team/marimo crewAIInc/crewAI langchain-ai/langchain simonw/datasette mlflow/mlflow run-llama/llama_index; do
  n=$(echo $r | tr '/' '_')
  if [ ! -d $n.git ]; then GIT_LFS_SKIP_SMUDGE=1 timeout 300 git clone --bare --filter=blob:none -q https://github.com/$r $n.git 2>/dev/null || { echo "$r CLONEFAIL"; continue; }; fi
  tot=$(git -C $n.git log --no-merges --since=2025-01-01 --format=%H | wc -l)
  claude=$(git -C $n.git log --no-merges --since=2025-01-01 -i -E --grep='co-authored-by: *claude|generated with \[?claude' --format=%H | wc -l)
  copilot=$(git -C $n.git log --no-merges --since=2025-01-01 --author='copilot' --format=%H | wc -l)
  other=$(git -C $n.git log --no-merges --since=2025-01-01 -i -E --grep='co-authored-by: *(cursor|devin|codex|gemini|openai)|generated with.*(cursor|codex|gemini)' --format=%H | wc -l)
  echo "$r total=$tot claude=$claude copilot=$copilot other=$other"
done
