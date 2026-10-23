"""Dictionary-based baseline features (M1) for RQ2: VADER sentiment + simple surface cues.
Requires `vaderSentiment` (pip install vaderSentiment)."""
import re

import pandas as pd


def add_lexicon_features(df):
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError as e:
        raise ImportError("pip install vaderSentiment to compute the lexicon baseline") from e
    sia = SentimentIntensityAnalyzer()
    t = df["text"].fillna("")
    out = df.copy()
    out["lex_compound"] = t.map(lambda s: sia.polarity_scores(s)["compound"])
    out["lex_exclaim"] = t.str.count("!")
    out["lex_caps_ratio"] = t.map(lambda s: sum(c.isupper() for c in s) / max(1, sum(c.isalpha() for c in s)))
    out["lex_digits"] = t.map(lambda s: len(re.findall(r"\d+", s)))
    return out


LEXICON_TERMS = ["lex_compound", "I(lex_compound**2)", "np.log1p(lex_exclaim)", "lex_caps_ratio", "np.log1p(lex_digits)"]
