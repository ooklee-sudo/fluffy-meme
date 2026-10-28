"""Pilot diagnostics for WDC JobPosting data as a firm-level source for H3. Usage: python pilot_stats.py POSTINGS.pkl OUT.json"""
import sys, re, json
import pandas as pd
df = pd.read_pickle(sys.argv[1])
df['host'] = df.url.str.extract(r'https?://([^/]+)')[0].str.replace(r'^www\.', '', regex=True)
df['year'] = pd.to_datetime(df.date.str[:10], errors='coerce').dt.year
VISUAL = r"graphic design|graphic artist|graphics design|illustrator|art director|motion (graphic|design)|video editor|videograph|photograph|animator|3d (artist|modell?er)|ui/ux|ux/ui|visual design|creative design|web design|brand design|concept artist|content creator|grafikdesign|mediengestalt|grafiker|graphiste|infographiste|diseñador gráfico|dise[ñn]ador|ilustrador|grafisch|webdesign|デザイナー|イラストレーター|動画"
GENAI = r"midjourney|stable diffusion|dall[-\s]?e|adobe firefly|firefly|generative ai|generative artificial|gen[-\s]?ai\b|genai|chat\s?gpt|openai|ai[-\s]generated|ai[-\s]tools?|text[-\s]to[-\s]image|text[-\s]to[-\s]video|runway ml|leonardo\.ai|canva ai|magic studio|generative ki|ki[-\s]generiert|ia generativa|生成ai|生成ＡＩ"
COMPLEMENT = r"compliance|legal counsel|data protection|privacy|dpo\b|ai governance|responsible ai|ethics|risk manager|brand manager|creative director|art director|head of design|design lead|quality assurance|datenschutz|juriste|jurist|rechtsanwalt"
txt = (df.title.fillna('') + ' ' + df.description.fillna('')).str.lower()
ttl = df.title.fillna('').str.lower()
df['visual'] = ttl.str.contains(VISUAL, regex=True)
df['genai'] = txt.str.contains(GENAI, regex=True)
df['comp'] = ttl.str.contains(COMPLEMENT, regex=True)
org = df.org.fillna('').str.strip().str.lower()
df['org_key'] = org.where(org != '')
S = {'n_postings': int(len(df)), 'n_hosts': int(df.host.nunique()), 'n_orgs_named': int(df.org_key.nunique()),
     'share_with_org_name': float(df.org_key.notna().mean()), 'share_with_date': float(df.year.notna().mean()),
     'share_with_description_200plus': float((df.description.fillna('').str.len() >= 200).mean()),
     'share_with_country': float(df.country.notna().mean()), 'year_distribution': {int(k): int(v) for k, v in df.year.value_counts().sort_index().tail(8).items()},
     'top_hosts': df.host.value_counts().head(8).to_dict(), 'top_countries': df.country.value_counts().head(8).to_dict(),
     'visual_postings': int(df.visual.sum()), 'visual_share': float(df.visual.mean()),
     'genai_mentions_all': float(df.genai.mean()), 'genai_mentions_visual': float(df[df.visual].genai.mean()) if df.visual.any() else None,
     'complement_title_share': float(df.comp.mean())}
named = df[df.org_key.notna()]
g = named.groupby('org_key').agg(n=('url', 'size'), vis=('visual', 'sum'), ai_vis=('genai', lambda s: 0), comp=('comp', 'sum'), ai=('genai', 'sum'))
vis_ai = named[named.visual].groupby('org_key').genai.sum()
g['ai_vis'] = vis_ai.reindex(g.index).fillna(0)
S['orgs_total'] = int(len(g)); S['orgs_with_visual'] = int((g.vis > 0).sum()); S['orgs_with_visual_and_2plus_postings'] = int(((g.vis > 0) & (g.n >= 2)).sum())
S['orgs_with_visual_and_any_genai_in_visual'] = int(((g.vis > 0) & (g.ai_vis > 0)).sum())
S['orgs_with_visual_and_complement_posting'] = int(((g.vis > 0) & (g.comp > 0)).sum())
S['orgs_with_visual_median_total_postings'] = float(g[g.vis > 0].n.median()) if (g.vis > 0).any() else None
S['cross_tab_visual_orgs_genai_by_complement'] = {f'comp={int(c)}': {'orgs': int(((g.vis > 0) & ((g.comp > 0) == c)).sum()), 'with_genai_visual': int(((g.vis > 0) & ((g.comp > 0) == c) & (g.ai_vis > 0)).sum())} for c in (False, True)}
S['sample_visual_genai_titles'] = df[df.visual & df.genai].title.head(8).tolist()
json.dump(S, open(sys.argv[2], 'w'), indent=1, default=str); print(json.dumps(S, indent=1, default=str))
