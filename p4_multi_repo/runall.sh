#!/bin/bash
for pair in "simonw_datasette simonw/datasette" "crewAIInc_crewAI crewAIInc/crewAI" "pydantic_pydantic-ai pydantic/pydantic-ai" "PrefectHQ_fastmcp PrefectHQ/fastmcp" "mlflow_mlflow mlflow/mlflow" "BerriAI_litellm BerriAI/litellm"; do
  set -- $pair
  MINF=8 MAXC=12000 python3 pipeline.py $1 $2 >> log_all.txt 2>&1
done
echo ALLDONE >> log_all.txt
