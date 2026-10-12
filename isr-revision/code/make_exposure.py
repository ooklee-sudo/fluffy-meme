"""Convert the first analysis kit's repo_relevance.csv into data/exposure.csv for launch_daily.py.

    python make_exposure.py C:\\Users\\leeook\\isr_analysis_kit\\repo_relevance.csv data\\exposure.csv
repo_relevance.csv: repo, category, open_weights, api_openai, api_anthropic, api_google
"""
import sys
import pandas as pd

R = pd.read_csv(sys.argv[1])
X = pd.DataFrame({"repo": R.repo, "open_weights": R.open_weights, "openai": R.api_openai,
                  "anthropic": R.api_anthropic, "google": R.api_google})
X.to_csv(sys.argv[2], index=False)
print(len(X), "repositories; exposed to:", X.drop(columns="repo").sum().to_dict())
