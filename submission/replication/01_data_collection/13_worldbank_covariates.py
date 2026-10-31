"""World Bank WDI API, 2023 values: GDP per capita (NY.GDP.PCAP.CD), internet users % (IT.NET.USER.ZS),
population (SP.POP.TOTL), for the 49 countries of the Google AI Overviews / AI Mode rollout panel.
Outputs: data/raw/wb_<indicator>.json, data/derived/country_covariates.csv   (Table 14)"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import json, requests, pandas as pd
for ind in ["NY.GDP.PCAP.CD","IT.NET.USER.ZS","SP.POP.TOTL"]:
    r=requests.get(f"https://api.worldbank.org/v2/country/all/indicator/{ind}?date=2023&format=json&per_page=400",timeout=60)
    print(r.status_code,ind); open(RAW/f"wb_{ind}.json","wb").write(r.content)
def load(ind):
    d=json.load(open(RAW/f"wb_{ind}.json"))[1]
    return pd.Series({x["country"]["id"]:x["value"] for x in d if x["value"] is not None})
gdp=load("NY.GDP.PCAP.CD"); net=load("IT.NET.USER.ZS"); pop=load("SP.POP.TOTL")
iso2=["US","GB","CA","AU","NZ","IE","IN","PK","BD","NG","KE","ZA","PH","SG","MY","ID","TH","VN","JP","KR","TW","HK","BR","MX","AR","CO","CL","PE","ES","PT","DE","AT","CH","FR","IT","NL","BE","PL","SE","DK","NO","FI","CZ","TR","SA","AE","EG","IL","UA"]
C=pd.DataFrame(index=iso2); C["gdppc"]=gdp; C["net_pct"]=net; C["pop"]=pop
C["net_users_m"]=C.net_pct/100*C["pop"]/1e6
C["eu_eea"]=C.index.isin(["IE","ES","PT","DE","AT","FR","IT","NL","BE","PL","SE","DK","NO","FI","CZ"]).astype(int)
C["english"]=C.index.isin(["US","GB","CA","AU","NZ","IE","IN","PK","NG","KE","ZA","PH","SG"]).astype(int)
print(C.round(1).to_string()); print("missing:",C[C.isna().any(axis=1)].index.tolist())
C.to_csv(DER/"country_covariates.csv")
