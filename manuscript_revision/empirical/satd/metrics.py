import re
STRICT = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
WIDE = re.compile(r"\b(todo|fixme|hack|xxx|workaround|temporary fix|for now)\b", re.I)
BROAD = re.compile(r"except\s*:|except\s+(Base)?Exception\b|catch\s*\(\s*(final\s+)?(Exception|Throwable)\b|rescue\s*(=>\s*\w+)?\s*$")
SUPPRESS = re.compile(r"#\s*type:\s*ignore|#\s*noqa|@ts-ignore|@ts-nocheck|eslint-disable|@SuppressWarnings|#\s*pylint:\s*disable|//\s*nolint|#\s*rubocop:disable|#\[allow\(")
TRIVIAL = re.compile(r"^[\s\{\}\(\)\[\];,]*$|^\s*(//|#|\*|/\*|\*/)")
def analyze(added):
    """added: list of added source lines (without the leading '+'). Same function for every data source."""
    n = len(added)
    if n == 0: return None
    txt = "\n".join(added)
    long_ = sum(len(l) > 120 for l in added)
    seen, dup = {}, 0
    for l in added:
        s = l.strip()
        if len(s) >= 40 and not TRIVIAL.match(l):
            seen[s] = seen.get(s, 0) + 1
    dup = sum(v - 1 for v in seen.values() if v > 1)
    return dict(added=n, strict=len(STRICT.findall(txt)), wide=len(WIDE.findall(txt)), long=long_, dup=dup,
                broad=len(BROAD.findall(txt)) if True else 0, suppress=len(SUPPRESS.findall(txt)))
