"""Create a temporary A40 pod running gpu/pod_server.py. Reads RUNPOD_API_KEY from the environment; writes the pod id and a fresh access token to /tmp (not the repository)."""
import json, os, secrets, base64, subprocess, sys
tok = secrets.token_hex(16); open("/tmp/pod_token", "w").write(tok); os.chmod("/tmp/pod_token", 0o600)
srv = base64.b64encode(open(os.path.join(os.path.dirname(__file__), "pod_server.py"), "rb").read()).decode()
body = {"name": "screening-baselines-tmp", "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04", "gpuTypeIds": sys.argv[1].split(",") if len(sys.argv) > 1 else ["NVIDIA A40"], "gpuCount": 1,
        "containerDiskInGb": 80, "volumeInGb": 0, "ports": ["8000/http"], "cloudType": "SECURE", "interruptible": False,
        "env": {"TOKEN": tok, "SERVER_B64": srv},
        "dockerStartCmd": ["bash", "-c", "echo \"$SERVER_B64\" | base64 -d > /workspace/server.py && python3 /workspace/server.py"]}
r = subprocess.run(["curl", "-s", "-m", "60", "-X", "POST", "https://rest.runpod.io/v1/pods", "-H", "Authorization: Bearer " + os.environ["RUNPOD_API_KEY"], "-H", "Content-Type: application/json", "-d", json.dumps(body)], capture_output=True, text=True)
d = json.loads(r.stdout); print({k: d.get(k) for k in ("id", "name", "costPerHr", "desiredStatus")})
open("/tmp/pod_id", "w").write(d["id"])
