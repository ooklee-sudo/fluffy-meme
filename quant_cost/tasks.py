"""Evaluation tasks for the quantization performance-cost experiment.

Four synthetic tasks (no downloads, deterministic given a seed) that differ in difficulty and in how
sensitive the input data is, plus a loader for user-supplied JSONL tasks (e.g. real, de-identified
company data).

Each task is a dict:
    name         task id
    sensitivity  "low" | "high"  (does the prompt contain personal/confidential data?)
    max_tokens   generation budget
    items        list of {"prompt", "answer", "pii"}   (pii = strings that would leave the firm if sent to an API)
    score(output, item) -> float in [0, 1]; an item counts as "correct" iff score == 1
"""
import json
import random
import re

# --------------------------------------------------------------------------- helpers

def _norm(s):
    return re.sub(r"[\s,\.\"'`]+", "", str(s)).lower()


def _last_int(text):
    m = re.findall(r"-?\d[\d,]*", text)
    if not m:
        return None
    try:
        return int(m[-1].replace(",", ""))
    except ValueError:
        return None


# --------------------------------------------------------------------------- 1. ticket classification
LABELS = ["billing", "shipping", "technical", "account"]

_TICKETS = {
    "billing": [
        "지난달 결제가 두 번 청구되었습니다. 환불해 주세요.",
        "I was charged twice for my subscription this month.",
        "영수증에 표시된 금액이 실제 결제 금액과 다릅니다.",
        "Please refund my last payment, the invoice amount is wrong.",
    ],
    "shipping": [
        "주문한 상품이 일주일째 도착하지 않았습니다.",
        "My package says delivered but I never received it.",
        "배송지 주소를 변경하고 싶은데 이미 출고되었다고 나옵니다.",
        "The courier has not updated the tracking status for five days.",
    ],
    "technical": [
        "앱을 열면 계속 오류 코드 502가 뜨면서 종료됩니다.",
        "The mobile app crashes every time I try to upload a photo.",
        "로그인 화면에서 화면이 하얗게 멈춥니다.",
        "The export button does nothing and the console shows a timeout error.",
    ],
    "account": [
        "비밀번호를 잊어버려서 재설정 메일이 필요합니다.",
        "I want to change the email address linked to my account.",
        "회원 탈퇴를 하고 싶습니다. 어떻게 해야 하나요?",
        "My account was locked after too many login attempts.",
    ],
}
_DISTRACT = [
    "", "", "감사합니다.", "Thanks in advance.", "급합니다!", "This is urgent.",
    "(다른 문의가 아니라 이 건입니다)", "Not sure if this is the right team.",
]


def ticket_task(n, seed=0):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        lab = rng.choice(LABELS)
        text = rng.choice(_TICKETS[lab])
        other = rng.choice([l for l in LABELS if l != lab])
        if rng.random() < 0.35:  # confounder: mention another category in passing
            text += " " + rng.choice(_TICKETS[other]).split(".")[0] + " 와(과) 관련은 없습니다."
        text = (text + " " + rng.choice(_DISTRACT)).strip()
        prompt = (f"Classify the customer message into exactly one category: {', '.join(LABELS)}.\n"
                  f"Reply with the category name only.\n\nMessage: {text}")
        items.append({"prompt": prompt, "answer": lab, "pii": []})

    def score(out, item):
        o = out.lower()
        hits = [(o.find(l), l) for l in LABELS if l in o]
        if not hits:
            return 0.0
        return 1.0 if min(hits)[1] == item["answer"] else 0.0

    return {"name": "ticket", "sensitivity": "low", "max_tokens": 8, "items": items, "score": score}


# --------------------------------------------------------------------------- 2. PII-bearing extraction
_SURN = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
_GIVEN = ["민준", "서연", "지호", "하은", "도윤", "수빈", "예준", "지우", "현우", "채원"]
_EN = ["Alice Morgan", "Daniel Park", "Grace Lee", "Henry Choi", "Sofia Kim", "Lucas Yoon"]


def extraction_task(n, seed=1):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        name = rng.choice(_EN) if rng.random() < 0.4 else rng.choice(_SURN) + rng.choice(_GIVEN)
        amount = rng.randrange(10, 990) * 100_000
        date = f"{rng.randint(2023, 2026)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        phone = f"010-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"
        email = f"user{rng.randint(100, 999)}@example.com"
        if rng.random() < 0.5:
            text = (f"계약 메모: 계약 상대방 {name} 씨(연락처 {phone}, {email})와 {date}에 "
                    f"총 {amount:,}원 규모의 용역 계약을 체결함. 중도 해지 시 위약금 {amount // 10:,}원 부과.")
        else:
            text = (f"Memo: contract signed on {date} with {name} (phone {phone}, email {email}); "
                    f"total value KRW {amount:,}. Early termination penalty KRW {amount // 10:,}.")
        prompt = ("Extract the counterparty name, the total contract amount (digits only, no commas, "
                  "NOT the penalty) and the signing date (YYYY-MM-DD).\n"
                  'Reply with JSON only: {"name": ..., "amount": ..., "date": ...}\n\n' + text)
        items.append({"prompt": prompt, "pii": [name, phone, email],
                      "answer": {"name": name, "amount": str(amount), "date": date}})

    def score(out, item):
        m = re.search(r"\{.*?\}", out, re.S)
        if not m:
            return 0.0
        try:
            got = json.loads(m.group(0))
        except Exception:
            return 0.0
        ok = sum(_norm(got.get(k, "")) == _norm(v) for k, v in item["answer"].items())
        return ok / len(item["answer"])

    return {"name": "extract", "sensitivity": "high", "max_tokens": 80, "items": items, "score": score}


# --------------------------------------------------------------------------- 3. multi-step arithmetic
def arith_task(n, seed=2):
    rng = random.Random(seed)
    items = []
    for _ in range(n):
        a, b, c, d = rng.randint(12, 60), rng.randint(5, 30), rng.randint(2, 9), rng.randint(2, 5)
        ans = (a + b) * c - d * 3
        if rng.random() < 0.5:
            q = (f"상점에 사과가 {a}개 있었는데 {b}개를 더 들여왔다. 이 전체를 {c}배로 늘리는 이벤트를 했고, "
                 f"그 뒤에 {d}개짜리 상자 3개를 팔았다. 남은 사과는 몇 개인가?")
        else:
            q = (f"A shop has {a} apples and receives {b} more. A promotion multiplies the whole stock by "
                 f"{c}. Then it sells 3 boxes of {d} apples each. How many apples remain?")
        prompt = q + "\nThink step by step briefly, then finish with 'Answer: <integer>'."
        items.append({"prompt": prompt, "answer": ans, "pii": []})

    def score(out, item):
        m = re.findall(r"answer\s*[:：]\s*(-?\d[\d,]*)", out, re.I)
        got = int(m[-1].replace(",", "")) if m else _last_int(out)
        return 1.0 if got == item["answer"] else 0.0

    return {"name": "arith", "sensitivity": "low", "max_tokens": 256, "items": items, "score": score}


# --------------------------------------------------------------------------- 4. user JSONL
def jsonl_task(path, name=None, sensitivity="high", max_tokens=64, limit=None):
    """Load {"prompt": ..., "answer": ..., "pii": [...]} lines. Score = normalized containment of `answer`."""
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                items.append({"prompt": r["prompt"], "answer": r["answer"], "pii": r.get("pii", [])})
    if limit:
        items = items[:limit]

    def score(out, item):
        return 1.0 if _norm(item["answer"]) in _norm(out) else 0.0

    return {"name": name or "custom", "sensitivity": sensitivity, "max_tokens": max_tokens,
            "items": items, "score": score}


def build_tasks(names, n, seed=0, task_files=()):
    makers = {"ticket": ticket_task, "extract": extraction_task, "arith": arith_task}
    out = []
    for nm in names:
        if nm not in makers:
            raise SystemExit(f"unknown task {nm!r}; choose from {sorted(makers)}")
        out.append(makers[nm](n, seed + sorted(makers).index(nm)))
    for p in task_files:
        out.append(jsonl_task(p, name=re.sub(r"\W+", "_", p.rsplit("/", 1)[-1].rsplit(".", 1)[0]), limit=n))
    return out
