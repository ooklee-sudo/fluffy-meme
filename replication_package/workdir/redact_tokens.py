"""Post-processing applied to every text file that contains sampled Stack Overflow posts or model answers before they were shared:
replaces strings that look like access tokens (JWT-like strings, Mapbox/AWS/GitHub/OpenAI-style keys, Slack tokens) with [REDACTED_TOKEN].
Usage: redact_tokens.py file1 [file2 ...]"""
import re, sys
pat = re.compile(r"(?:[ps]k\.)?eyJ[A-Za-z0-9_\-]{8,}(?:\.[A-Za-z0-9_\-]+)*|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{32,}|xox[baprs]-[A-Za-z0-9\-]{10,}")
for f in sys.argv[1:]:
    s = open(f, encoding="utf-8").read(); n = len(pat.findall(s))
    if n: open(f, "w", encoding="utf-8").write(pat.sub("[REDACTED_TOKEN]", s))
    print(f, "redacted", n)
