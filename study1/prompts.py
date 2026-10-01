"""System prompt (identical for every model and item) and the answer parser."""
import re

SYSTEM = ("You are an operations analyst at a regulated financial firm. You review the case you are given and recommend one of the listed options. "
          "Do not mention your model name, developer, or size. Keep your reasoning brief. "
          "End your reply with exactly two lines and nothing after them:\n"
          "RECOMMENDATION: <A, B, or C>\n"
          "CONFIDENCE: <an integer from 0 to 100>")

_REC = re.compile(r"RECOMMENDATION\s*:\s*\**\s*\(?([ABC])\b", re.I)
_CONF = re.compile(r"CONFIDENCE\s*:\s*\**\s*(\d{1,3})\b", re.I)


def strip_thinking(text):
    """Remove a completed <think>...</think> block. An unclosed block means the answer was never reached."""
    if "<think>" in text and "</think>" not in text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S)


def parse(text):
    """-> (letter or None, confidence or None). The last match wins."""
    t = strip_thinking(text or "")
    r, c = _REC.findall(t), _CONF.findall(t)
    letter = r[-1].upper() if r else None
    conf = int(c[-1]) if c else None
    if conf is not None and not 0 <= conf <= 100:
        conf = None
    return letter, conf
