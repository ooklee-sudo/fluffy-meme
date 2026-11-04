import sys; sys.path.insert(0,'.')
from km import *
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')+'/'
def gemini(stage='stable'):
    g=load([R+'gemini_lifecycle.csv'])
    t=g[g.tier.isin(['pro','flash','flash-lite','flash-8b'])].copy()
    t=t[~t.model_id.isin(['gemini-pro-vision'])]                      # vision alias of 1.0 Pro
    t=t.drop_duplicates(subset=['release_date','shutdown_date','tier'])  # aliases sharing a version's dates
    if stage=='stable': t=t[t.stage_at_release=='stable']
    elif stage=='preview': t=t[t.stage_at_release!='stable']
    return t
def openai():
    oa=load([R+'openai_lifecycle.csv']); oa['cat']=oa.notes.str.extract(r'cat=([\w-]+)')
    return oa[oa.cat.isin(['chat-text','text-completion'])]
def anthropic():
    ot=load([R+'other_lifecycle.csv']); a=ot[ot.platform=='Anthropic API']; return a[a.tier!='specialized']
def notice_days(d, drop_reroute=True):
    x=d[d.announce_date.notna()&d.shutdown_date.notna()]
    if drop_reroute: x=x[~x.notes.str.contains('redirect|reroute|auto-rout',case=False)]
    return (x.shutdown_date-x.announce_date).dt.days.values.astype(float)
SETS={'Gemini API (stable)':gemini('stable'),'Gemini API (preview/exp.)':gemini('preview'),
      'OpenAI API (chat/text)':openai(),'Anthropic API':anthropic()}
