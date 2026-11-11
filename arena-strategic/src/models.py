import re
def developer(m):
    m = m.lower()
    rules = [('openai', r'^(gpt|o\d|chatgpt)'), ('anthropic', r'^claude'), ('google', r'^(gemini|gemma)'), ('meta', r'^llama'),
             ('mistral', r'^(mistral|magistral)'), ('alibaba', r'^(qwen|qwq)'), ('deepseek', r'^deepseek'), ('xai', r'^grok'),
             ('cohere', r'^command'), ('amazon', r'^amazon'), ('minimax', r'^minimax'), ('moonshot', r'^kimi'), ('tencent', r'^hunyuan')]
    for d, rx in rules:
        if re.search(rx, m): return d
    return 'other'
# top developers by leaderboard position during Apr-Jul 2025 (for H1a)
TOP3 = {'google', 'openai', 'anthropic'}
