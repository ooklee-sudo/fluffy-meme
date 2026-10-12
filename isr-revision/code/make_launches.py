"""Convert the first analysis kit's events.csv into data/launches.csv for launch_daily.py.

    python make_launches.py C:\\Users\\leeook\\isr_analysis_kit\\events.csv data\\launches.csv
events.csv: event_id, date, type (open_weights | api_openai | api_anthropic | api_google), model, keywords (regex), source_note
"""
import sys
import pandas as pd

E = pd.read_csv(sys.argv[1])
L = pd.DataFrame({"launch_id": E.event_id, "date": E.date,
                  "type": E.type.str.replace("api_", "", regex=False),
                  "keywords": E.keywords})
L.to_csv(sys.argv[2], index=False)
print(len(L), "launches;", L.type.value_counts().to_dict())
