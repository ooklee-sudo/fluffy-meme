"""Detector patterns copied verbatim from retraining_rust/wildchat_drift.py (the manuscript's original code)."""
import re
YEAR = re.compile(r"\b(2022|2023|2024)\b")
ENT = re.compile(r"\b(midjourney|bing chat|bard|llama|claude|stable diffusion|dall-?e ?2|github copilot|gemini pro|mistral)\b", re.I)
JB = re.compile(r"\b(DAN|jailbreak|do anything now|developer mode|stay in character)\b")
DISSAT = re.compile(
    r"^\W*(no\b|nope\b|wrong\b|incorrect\b|that'?s (not|wrong|incorrect)|that is (not|wrong|incorrect)|"
    r"that was (not|wrong)|you('| a)re wrong|this is (not|wrong|incorrect)|not (what|correct|right|true)|"
    r"that (doesn'?t|does not|didn'?t|did not)|it (doesn'?t|does not|didn'?t) work|doesn'?t work|"
    r"try again|redo|you (misunderstood|didn'?t|did not)|i (said|asked|meant)|wrong answer|"
    r"that('s| is) (not|incorrect) (what|correct|right)|error\b)", re.I)
# v2 detector: v1 start-of-turn patterns, plus cues anywhere in the first 200 characters
# (designed from the codebook categories: "I meant", pasted error output, "still/same error",
# "didn't work", "you didn't/forgot", "I said/asked", "are you sure", "that's not", "wrong/incorrect").
DISSAT2_ANY = re.compile(
    r"\b(i mean[t]?\b|still (not|doesn'?t|isn'?t|getting|the same|error|wrong|fail)|same error|"
    r"(did(n'?t| not)|does(n'?t| not)|do(n'?t| not)) work|not working|it (didn'?t|doesn'?t|did not|does not)|"
    r"you (didn'?t|did not|forgot|missed|ignored|misunderstood)|i (said|asked|requested|didn'?t (ask|say|tell|want))|"
    r"are you sure|that'?s not|this is not|that is not|not true|incorrect|wrong|mistake|hallucinat\w*|"
    r"traceback \(most recent|\bsyntaxerror|\btypeerror|\bnameerror|\bvalueerror|\battributeerror|\bkeyerror|"
    r"\bexception\b|\berror[:\s]|\bfailed\b|cannot read propert|no such file|not found|http \d{3} error)", re.I)



def dissat2(u):
    return bool(DISSAT.search(u[:120]) or DISSAT2_ANY.search(u[:200]))

CODE = re.compile(r"```|\bdef \w+\(|\bimport \w+|#include|\bfunction\s*\(|</?\w+>|\bSELECT\b.*\bFROM\b", re.I | re.S)
