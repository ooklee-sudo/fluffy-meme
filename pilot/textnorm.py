"""Shared text normalization, applied identically to human chunks and machine rewrites.

Removes artifacts that would let a detector separate the two corpora for reasons
unrelated to writing style: chatbot preambles/closers, markdown, paragraph numbers,
all-caps section headings, and glued reference numerals.
"""
import re

PREFACE = re.compile(r"^\s*(here is|here's|here are|sure|certainly|of course|below is|okay|ok)\b[^\n]*:?\s*\n+", re.I)
CLOSER = re.compile(r"\n+\s*(note|notes|i (have|'ve) (made|kept|preserved|revised)|let me know)\b.*\Z", re.I | re.S)
HEADING_WORDS = 15


def _is_heading(line):
    s = line.strip()
    if not s or len(s.split()) > HEADING_WORDS:
        return False
    letters = re.sub(r"[^A-Za-z]", "", s)
    return len(letters) >= 4 and letters.isupper() and not s.endswith((".", ";", ","))


def normalize(text):
    t = text or ""
    t = PREFACE.sub("", t, count=1)
    t = CLOSER.sub("", t)
    t = re.sub(r"\*\*|__|^#{1,6}\s*", "", t, flags=re.M)          # markdown
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\[\d{3,5}\]", " ", t)                            # paragraph numbers
    t = "\n".join(l for l in t.splitlines() if not _is_heading(l))  # all-caps heading lines
    t = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", t)  # glued numerals
    return re.sub(r"\s+", " ", t).strip()
