"""Load the public Arena releases into one tidy frame with assistant turns as plain text."""
import glob, json, numpy as np, pandas as pd, pyarrow.parquet as pq
D = '/home/user/data'

def _txt(c):
    if isinstance(c, str): return c
    if c is None: return ''
    return ' '.join((x.get('text') or '') for x in c if isinstance(x, dict))

def _turns(conv, role):
    return [_txt(m['content']) for m in conv if m['role'] == role]

def load100():
    df = pq.read_table(f'{D}/a100.parquet', columns=['question_id','model_a','model_b','winner','conversation_a','conversation_b','turn','anony','language','tstamp','conv_metadata','is_refusal','dedup_tag','judge_hash']).to_pandas()
    out = pd.DataFrame({'id': df.question_id, 'src': '100k', 'model_a': df.model_a, 'model_b': df.model_b, 'winner': df.winner,
        'turn': df.turn, 'anony': df.anony, 'language': df.language, 'ts': pd.to_datetime(df.tstamp, unit='s'), 'user': df.judge_hash})
    out['user_turns'] = [_turns(c, 'user') for c in df.conversation_a]
    out['a_turns'] = [_turns(c, 'assistant') for c in df.conversation_a]
    out['b_turns'] = [_turns(c, 'assistant') for c in df.conversation_b]
    out['meta'] = df.conv_metadata
    out['refusal'] = df.is_refusal
    return out

def load140():
    fs = sorted(glob.glob(f'{D}/a140_*.parquet'))
    parts = []
    for f in fs:
        df = pq.read_table(f, columns=['id','model_a','model_b','winner','evaluation_session_id','evaluation_order','conversation_a','conversation_b','conv_metadata','language','timestamp']).to_pandas()
        o = pd.DataFrame({'id': df.id, 'src': '140k', 'model_a': df.model_a, 'model_b': df.model_b, 'winner': df.winner,
            'turn': [sum(m['role']=='user' for m in c) for c in df.conversation_a], 'anony': True, 'language': df.language,
            'ts': pd.to_datetime(df.timestamp), 'user': df.evaluation_session_id, 'order': df.evaluation_order})
        o['user_turns'] = [_turns(c, 'user') for c in df.conversation_a]
        o['a_turns'] = [_turns(c, 'assistant') for c in df.conversation_a]
        o['b_turns'] = [_turns(c, 'assistant') for c in df.conversation_b]
        o['meta'] = df.conv_metadata
        parts.append(o)
    return pd.concat(parts, ignore_index=True)

def load55():
    df = pd.read_csv(f'{D}/a55.csv')
    def j(s):
        try: return [x if isinstance(x, str) else '' for x in json.loads(s)]
        except Exception: return []
    w = np.select([df.winner_model_a == 1, df.winner_model_b == 1], ['model_a', 'model_b'], 'tie')
    o = pd.DataFrame({'id': df.id.astype(str), 'src': '55k', 'model_a': df.model_a, 'model_b': df.model_b, 'winner': w,
        'anony': True, 'language': None, 'ts': pd.NaT, 'user': None})
    o['user_turns'] = [j(s) for s in df.prompt]; o['a_turns'] = [j(s) for s in df.response_a]; o['b_turns'] = [j(s) for s in df.response_b]
    o['turn'] = o.user_turns.str.len()
    return o

if __name__ == '__main__':
    import sys
    for name, fn in [(a, globals()['load'+a[:-1]]) for a in (sys.argv[1:] or ['100k','140k','55k'])]:
        d = fn(); d.to_pickle(f'{D}/{name}.pkl'); print(name, len(d), d.ts.min(), d.ts.max())
