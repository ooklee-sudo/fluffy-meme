"""Minimal server for the Study 2 survey: static files, balanced assignment, and response storage.

  python quant_cost/webapp/server.py --port 8765 --data-dir quant_cost/webapp/data

Uses only the Python standard library. Responses are stored as one JSON file per participant under
<data-dir>/participants/. The server does not log or store IP addresses.

For real data collection put it behind HTTPS (a reverse proxy or a tunnel); see README.md for options and the
data-protection points to decide first.
"""
import argparse
import json
import os
import random
import re
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")
NEWS = ("incident", "control")
VERSIONS = ("V1", "V2", "V3", "V4")
MAX_BODY = 400_000
LOCK = threading.Lock()
DATA_DIR = os.path.join(HERE, "data")


def safe(s, n=64):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(s))[:n] or "x"


def atomic_write(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_assign():
    p = os.path.join(DATA_DIR, "assignments.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"counts": {f"{n}|{v}": 0 for n in NEWS for v in VERSIONS}, "by_participant": {}}


def assign(pid, session):
    """Least-filled of the 8 (news x Latin-square version) groups; ties broken at random; idempotent per participant."""
    key = f"{safe(pid)}|{safe(session)}"
    with LOCK:
        a = load_assign()
        if key in a["by_participant"]:
            return a["by_participant"][key]
        low = min(a["counts"].values())
        news, version = random.choice([k for k, v in a["counts"].items() if v == low]).split("|")
        res = {"news": news, "version": version, "order": random.sample(range(4), 4),
               "assignedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        a["counts"][f"{news}|{version}"] += 1
        a["by_participant"][key] = res
        atomic_write(os.path.join(DATA_DIR, "assignments.json"), a)
        return res


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC, **kwargs)

    def log_message(self, *args):  # no access log: no IP addresses are written anywhere
        pass

    def list_directory(self, path):
        self.send_error(404)
        return None

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/ping":
            return self._json(200, {"ok": True})
        if self.path.startswith("/api/"):
            return self._json(404, {"ok": False})
        return super().do_GET()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            return None
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return None

    def do_POST(self):
        path = self.path.split("?")[0]
        data = self._body()
        if data is None or not isinstance(data, dict):
            return self._json(400, {"ok": False, "error": "bad body"})
        if path == "/api/assign":
            return self._json(200, assign(data.get("pid", ""), data.get("sessionId", "")))
        if path == "/api/save":
            pid, session = safe(data.get("pid", "")), safe(data.get("sessionId", ""))
            data["serverReceivedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with LOCK:
                atomic_write(os.path.join(DATA_DIR, "participants", f"{pid}__{session}.json"), data)
            return self._json(200, {"ok": True})
        return self._json(404, {"ok": False})


def main():
    global DATA_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1", help="127.0.0.1 = this computer only (default)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--data-dir", default=os.path.join(HERE, "data"))
    a = ap.parse_args()
    DATA_DIR = os.path.abspath(a.data_dir)
    os.makedirs(os.path.join(DATA_DIR, "participants"), exist_ok=True)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"Study 2 survey on http://{a.host}:{a.port}/  (data in {DATA_DIR})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
