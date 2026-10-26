"""Minimal token-protected file server for a temporary GPU pod: PUT /in/<name>, GET /out/<name>, GET /log, POST /run/<script>."""
import os, subprocess, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
TOKEN = os.environ["TOKEN"]; IN, OUT = "/workspace/in", "/workspace/out"
os.makedirs(IN, exist_ok=True); os.makedirs(OUT, exist_ok=True)
class H(BaseHTTPRequestHandler):
    def ok(self): return self.headers.get("X-Token") == TOKEN
    def send(self, code, body=b""):
        self.send_response(code); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def name(self, prefix):
        n = os.path.basename(self.path[len(prefix):]); return n if n and not n.startswith(".") else None
    def do_PUT(self):
        if not self.ok() or not self.path.startswith("/in/"): return self.send(403)
        n = self.name("/in/"); body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        open(os.path.join(IN, n), "wb").write(body); self.send(200, b"ok")
    def do_GET(self):
        if not self.ok(): return self.send(403)
        if self.path == "/log":
            p = "/workspace/run.log"; return self.send(200, open(p, "rb").read()[-20000:] if os.path.exists(p) else b"")
        if self.path == "/ls": return self.send(200, "\n".join(sorted(os.listdir(OUT))).encode())
        if self.path.startswith("/out/"):
            n = self.name("/out/"); p = os.path.join(OUT, n or "")
            return self.send(200, open(p, "rb").read()) if n and os.path.exists(p) else self.send(404)
        self.send(200, b"pod server up")
    def do_POST(self):
        if not self.ok() or not self.path.startswith("/run/"): return self.send(403)
        n = self.name("/run/"); p = os.path.join(IN, n or "")
        if not n or not os.path.exists(p): return self.send(404)
        subprocess.Popen(f"bash {p} >> /workspace/run.log 2>&1", shell=True, cwd=IN); self.send(200, b"started")
    def log_message(self, *a): pass
ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
