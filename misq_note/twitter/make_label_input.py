import pandas as pd, json
f=pd.read_csv('frame_oil_iran.csv',dtype={'id':str})
json.dump([{'id':r.id,'text':r.text} for r in f.itertuples()],open('label_input.json','w'),ensure_ascii=False,indent=0); print(len(f))
