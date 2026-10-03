"""Selects the item bank. Default: the Study 1 bank (items.py). Set STUDY1_BANK=hard for the Study 1b bank (items_hard.py).
Study 1 files are never modified by the hard bank; the hard bank writes items_hard.jsonl, gold_hard.json, MANIFEST_hard.json."""
import os
NAME = os.environ.get("STUDY1_BANK", "main")
if NAME == "hard":
    from items_hard import build, render, social_text, SOCIAL, SOCIAL_SETS, SENT_NAMES, DOMAINS
    ITEMS_FILE, GOLD_FILE, MANIFEST_FILE = "items_hard.jsonl", "gold_hard.json", "MANIFEST_hard.json"
elif NAME == "pilot":
    import items_hard as _h
    from items_hard import render, social_text, SOCIAL, SOCIAL_SETS, SENT_NAMES, DOMAINS
    build = lambda: _h.build(pilot=True)
    ITEMS_FILE, GOLD_FILE, MANIFEST_FILE = "items_pilot.jsonl", "gold_hard.json", "MANIFEST_pilot.json"
else:
    from items import build, render, social_text, SOCIAL, SOCIAL_SETS, DOMAINS
    SENT_NAMES = ["already decided", "obviously right", "client is right", "please confirm"]
    ITEMS_FILE, GOLD_FILE, MANIFEST_FILE = "items.jsonl", "gold.json", "MANIFEST.json"
