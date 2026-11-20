"""Environment check before measuring: GPU, drivers, which backend works, power meter, disk.

  python -m quant_cost.doctor
Exit code 0 if at least one backend can run on the GPU (or CPU when --cpu is given), 1 otherwise.
"""
import importlib
import platform
import shutil
import subprocess
import sys


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e:  # noqa: BLE001
        return 1, "", str(e)


def say(level, msg):
    print(f"[{level:4s}] {msg}")


def check_gpu():
    info = {"ok": False}
    if shutil.which("nvidia-smi") is None:
        say("FAIL", "nvidia-smi not found: NVIDIA driver is not installed or not on PATH.")
        return info
    code, out, err = _run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,power.limit",
                           "--format=csv,noheader,nounits"])
    if code != 0 or not out:
        say("FAIL", f"nvidia-smi failed: {err or out}")
        return info
    name, drv, tot, used, plim = [x.strip() for x in out.splitlines()[0].split(",")]
    info.update(ok=True, name=name, driver=drv, mem_total_mib=float(tot), mem_used_mib=float(used))
    say("OK", f"GPU: {name}, driver {drv}, {float(tot)/1024:.1f} GiB VRAM ({float(used)/1024:.1f} GiB already in use), "
              f"power limit {plim} W")
    if float(used) > 1500:
        say("WARN", "More than 1.5 GiB of VRAM is already used. Close browsers/games/other GPU apps before measuring.")
    code, out, _ = _run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"])
    try:
        float(out.splitlines()[0])
        info["power_meter"] = True
        say("OK", f"nvidia-smi reports GPU power ({out.splitlines()[0]} W): energy can be measured.")
    except Exception:  # noqa: BLE001
        info["power_meter"] = False
        say("WARN", f"nvidia-smi does not report GPU power on this laptop ({out!r}). "
                    "Use a wall-plug meter and pass --wall-watts to the runner for energy.")
    return info


def check_llamacpp():
    try:
        llama_cpp = importlib.import_module("llama_cpp")
    except Exception as e:  # noqa: BLE001
        say("INFO", f"llama-cpp-python not importable ({type(e).__name__}).")
        return {"ok": False, "gpu": False}
    gpu = False
    try:
        gpu = bool(llama_cpp.llama_supports_gpu_offload())
    except Exception:  # noqa: BLE001
        pass
    say("OK" if gpu else "WARN", f"llama-cpp-python {getattr(llama_cpp, '__version__', '?')}: "
                                 f"GPU offload {'AVAILABLE' if gpu else 'NOT available (CPU-only build)'}")
    if not gpu:
        say("INFO", 'To get GPU offload: set CMAKE_ARGS="-DGGML_CUDA=on" and reinstall llama-cpp-python '
                    "(needs CUDA Toolkit and a C++ compiler on Windows), or use the PyTorch route.")
    return {"ok": True, "gpu": gpu}


def check_torch():
    try:
        torch = importlib.import_module("torch")
    except Exception as e:  # noqa: BLE001
        say("INFO", f"torch not importable ({type(e).__name__}).")
        return {"ok": False, "cuda": False, "bnb": False}
    cuda = torch.cuda.is_available()
    say("OK" if cuda else "WARN", f"torch {torch.__version__}: CUDA {'available (' + torch.cuda.get_device_name(0) + ')' if cuda else 'NOT available (CPU-only build or driver mismatch)'}")
    if not cuda:
        say("INFO", "Install a CUDA build of torch from https://pytorch.org (command depends on your driver).")
    bnb_ok = False
    if cuda:
        try:
            bnb = importlib.import_module("bitsandbytes")
            lin = bnb.nn.Linear4bit(64, 64, compute_dtype=torch.float16, quant_type="nf4").cuda()
            lin(torch.randn(1, 64, dtype=torch.float16).cuda())
            bnb_ok = True
            say("OK", f"bitsandbytes {getattr(bnb, '__version__', '?')}: 4-bit layer ran on the GPU.")
        except Exception as e:  # noqa: BLE001
            say("WARN", f"bitsandbytes does not work here ({type(e).__name__}: {str(e)[:120]}). "
                        "fp16 measurements still work; int8/nf4/fp4 need bitsandbytes.")
    return {"ok": True, "cuda": cuda, "bnb": bnb_ok}


def check_other():
    for mod in ("huggingface_hub", "matplotlib"):
        try:
            importlib.import_module(mod)
            say("OK", f"{mod} installed")
        except Exception:  # noqa: BLE001
            say("FAIL", f"{mod} missing: pip install {mod}")
    free = shutil.disk_usage(".").free / 2**30
    say("OK" if free > 40 else "WARN", f"free disk here: {free:.0f} GiB (full runs download tens of GiB; files are deleted after each model).")


def diagnose(verbose=True):
    print(f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()}")
    gpu = check_gpu()
    lc = check_llamacpp()
    to = check_torch()
    check_other()
    routes = []
    if gpu["ok"] and lc.get("gpu"):
        routes.append("llamacpp")
    if gpu["ok"] and to.get("cuda"):
        routes.append("torch")
    print()
    if routes:
        say("OK", f"Usable GPU routes: {', '.join(routes)}  (recommended: {routes[0]})")
    else:
        say("FAIL", "No GPU route works yet. Fix the WARN/FAIL lines above (torch with CUDA is usually the easiest).")
    return {"gpu": gpu, "llamacpp": lc, "torch": to, "routes": routes}


if __name__ == "__main__":
    d = diagnose()
    sys.exit(0 if d["routes"] else 1)
