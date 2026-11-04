"""Print the Gemini 2.0 Flash / 2.0 Flash-Lite price rows from an archived Google pricing page (takes a few seconds)."""
import html, re, urllib.request
URL = "https://web.archive.org/web/20260311202101id_/https://ai.google.dev/gemini-api/docs/pricing"
req = urllib.request.Request(URL, headers={"User-Agent": "lifecycle-data-verification/1.0 (academic research)"})
page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
text = re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", page)))
for mid in ["gemini-2.0-flash ", "gemini-2.0-flash-lite "]:
    i = text.find(mid)
    print("=" * 20, mid.strip(), "=" * 20)
    print(text[i:i + 900] if i >= 0 else "not found")
    print()
