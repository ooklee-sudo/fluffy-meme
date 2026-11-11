"""Stage-1 identity-leak detector (regex). Flags first-person self-disclosure of a model or developer name."""
import re
DEV = {
 'openai': r'openai|chat ?gpt|gpt-?[345o]', 'anthropic': r'anthropic|claude', 'google': r'google|gemini|gemma|bard|deepmind|palm',
 'meta': r'meta(?: ai)?|llama', 'mistral': r'mistral|mixtral', 'alibaba': r'alibaba|qwen|tongyi', 'deepseek': r'deepseek',
 'xai': r'xai|x\.ai|grok', 'zhipu': r'zhipu|chatglm|glm', 'cohere': r'cohere|command[ -]r', 'microsoft': r'microsoft|phi-?\d',
 'amazon': r'amazon|nova', 'nvidia': r'nvidia|nemotron', '01ai': r'01\.ai|\byi\b', 'reka': r'reka', 'ai21': r'ai21|jamba',
 'moonshot': r'moonshot|kimi', 'minimax': r'minimax', 'tencent': r'tencent|hunyuan', 'lmsys': r'lmsys|vicuna', 'baidu': r'baidu|ernie',
}
ANY = '|'.join(f'(?:{v})' for v in DEV.values())
# first-person disclosure patterns
P = [
 rf"\bi(?:'m| am)\s+(?:an?\s+)?(?:ai\s+|large\s+language\s+model\s+|language\s+model\s+|assistant\s+)?(?:called\s+|named\s+)?\**(?:{ANY})\b",
 rf"\b(?:developed|created|trained|built|made|designed)\s+by\s+(?:the\s+)?(?:team\s+at\s+)?\**(?:{ANY})\b",
 rf"\bmy\s+name\s+is\s+\**(?:{ANY})\b",
 rf"\bas\s+(?:an?\s+)?\**(?:{ANY})\b[^.\n]{{0,40}}\b(?:model|assistant|ai)\b",
 rf"\bi(?:'m| am)\s+(?:an?\s+)?\**(?:{ANY})\**(?:[ ,-]+\w+){{0,3}}\s*,?\s+(?:a|an)\s+(?:large\s+)?(?:language\s+model|ai)",
]
RX = re.compile('|'.join(f'(?:{p})' for p in P), re.I)
RX_ANY = re.compile(rf'\b(?:{ANY})\b', re.I)
ASK = re.compile(r"\b(?:who|what)\s+(?:are|r)\s+(?:you|u)\b|\bwhich\s+(?:model|llm|ai)\b|\bwho\s+(?:made|created|trained|built|developed)\s+you\b|\byour\s+(?:name|creator|developer|model)\b|\bare\s+you\s+(?:gpt|chatgpt|claude|gemini|llama)", re.I)

def dev_of(text):
    m = RX.search(text)
    if not m: return None
    s = m.group(0).lower()
    for k, v in DEV.items():
        if re.search(rf'\b(?:{v})\b', s): return k
    return 'unk'

def first_leak(turns):
    """(turn index, developer) of first self-disclosure, or (None, None)."""
    for i, t in enumerate(turns):
        d = dev_of(t or '')
        if d: return i, d
    return None, None
