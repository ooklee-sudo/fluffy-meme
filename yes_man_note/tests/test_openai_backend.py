"""OpenAI-compatible / OpenRouter path against a local fake server (no network, no key)."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import ym_common as yc  # noqa: E402

SEEN = []


class Fake(BaseHTTPRequestHandler):
    calls = 0

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
        Fake.calls += 1
        if Fake.calls == 1:   # an error delivered inside a 200 response, as some routers do
            out = {"error": {"code": 502, "message": "upstream hiccup"}}
        else:
            user = body["messages"][1]["content"]
            letter = "B" if "Options:" in user else "A"
            out = {"model": "fake/served-model", "provider": "FakeHost",
                   "choices": [{"message": {"content": letter}, "finish_reason": "stop"}],
                   "usage": {"prompt_tokens": 120, "completion_tokens": 1}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class OpenAIPath(unittest.TestCase):
    def test_roundtrip(self):
        srv = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        tmp = tempfile.mkdtemp()
        items = os.path.join(tmp, "items.jsonl")
        subprocess.run([sys.executable, "make_mock_items.py", "--n", "3", "--out", items], cwd=ROOT, check=True,
                       capture_output=True)
        models = os.path.join(tmp, "models.json")
        with open(models, "w") as f:
            json.dump({"models": [{"name": "fake", "family": "F", "tier": "S", "tier_rank": 0, "backend": "openai",
                                   "base_url": f"http://127.0.0.1:{srv.server_port}/v1", "api_key_env": "FAKE_KEY",
                                   "model_id": "fake/model", "temperature": 1.0,
                                   "extra_body": {"provider": {"order": ["FakeHost"], "allow_fallbacks": False}}}]}, f)
        out = os.path.join(tmp, "res.jsonl")
        env = dict(os.environ, FAKE_KEY="sk-test")
        r = subprocess.run([sys.executable, "runner.py", "--items", items, "--models", models, "--out", out,
                            "--channels", "C1", "--reps", "2", "--workers", "1"], cwd=ROOT, env=env,
                           capture_output=True, text=True)
        srv.shutdown()
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out) as f:
            rows = [json.loads(line) for line in f]
        self.assertEqual(len(rows), 6)                       # 3 items x 2 replicates
        self.assertTrue(all(x["api_ok"] for x in rows))      # the in-body 502 was retried
        self.assertTrue(all(x["served_by"] == "FakeHost" and x["served_model"] == "fake/served-model" for x in rows))
        self.assertTrue(all(x["tokens_in"] == 120 and x["tokens_out"] == 1 for x in rows))
        first = SEEN[1]
        self.assertEqual(first["path"], "/v1/chat/completions")
        self.assertEqual(first["auth"], "Bearer sk-test")
        self.assertEqual(first["body"]["model"], "fake/model")
        self.assertEqual(first["body"]["temperature"], 1.0)
        self.assertEqual(first["body"]["provider"], {"order": ["FakeHost"], "allow_fallbacks": False})
        self.assertEqual(first["body"]["messages"][0]["role"], "system")


if __name__ == "__main__":
    unittest.main()
