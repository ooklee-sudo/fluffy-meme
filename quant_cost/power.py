"""Power / memory metering.

Sources (used if available):
  - NVIDIA GPU:   one persistent `nvidia-smi -lms` process -> GPU board power (W) and memory used (MiB)
  - Intel RAPL:   /sys/class/powercap/intel-rapl:0/energy_uj -> CPU package energy (Linux, usually needs root)
Otherwise nothing is measured for that source and the caller falls back to an assumed wattage.
For the most defensible numbers use a wall-plug meter and pass its average to bench.py with --wall-watts.
"""
import shutil
import subprocess
import threading
import time

RAPL = "/sys/class/powercap/intel-rapl:0/"


def _read(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return None


class PowerMeter:
    def __init__(self, interval_ms=200, gpu_index=0):
        self.interval_ms = interval_ms
        self.gpu_index = gpu_index
        self.has_gpu = shutil.which("nvidia-smi") is not None
        self.has_rapl = _read(RAPL + "energy_uj") is not None
        self._proc = None
        self._thread = None
        self._stop = threading.Event()
        self.samples = []  # (t, watts, mem_mib)

    def start(self):
        self.samples = []
        self._stop.clear()
        self.t0 = time.perf_counter()
        self.rapl0 = _read(RAPL + "energy_uj") if self.has_rapl else None
        self.rapl_max = _read(RAPL + "max_energy_range_uj") if self.has_rapl else None
        if self.has_gpu:
            self._proc = subprocess.Popen(
                ["nvidia-smi", f"--id={self.gpu_index}", "--query-gpu=power.draw,memory.used",
                 "--format=csv,noheader,nounits", f"-lms={self.interval_ms}"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            self._thread = threading.Thread(target=self._pump, daemon=True)
            self._thread.start()
        return self

    def _pump(self):
        for line in self._proc.stdout:
            if self._stop.is_set():
                break
            try:
                w, m = (float(x) for x in line.strip().split(","))
            except ValueError:
                continue
            self.samples.append((time.perf_counter(), w, m))

    def stop(self):
        dur = time.perf_counter() - self.t0
        self._stop.set()
        if self._proc:
            self._proc.terminate()
            self._proc.wait()
        out = {"duration_s": dur, "gpu_energy_j": None, "gpu_avg_w": None,
               "gpu_peak_mem_mib": None, "cpu_energy_j": None}
        if len(self.samples) >= 2:
            e = 0.0
            for (t1, w1, _), (t2, w2, _) in zip(self.samples, self.samples[1:]):
                e += 0.5 * (w1 + w2) * (t2 - t1)
            span = self.samples[-1][0] - self.samples[0][0]
            out["gpu_energy_j"] = e
            out["gpu_avg_w"] = e / span if span > 0 else None
            out["gpu_peak_mem_mib"] = max(m for _, _, m in self.samples)
        if self.has_rapl and self.rapl0 is not None:
            now = _read(RAPL + "energy_uj")
            if now is not None:
                d = now - self.rapl0
                if d < 0 and self.rapl_max:
                    d += self.rapl_max
                out["cpu_energy_j"] = d / 1e6
        return out


def measure_idle(seconds=5.0, **kw):
    """Average idle power (W) of GPU and CPU package, to subtract from busy measurements."""
    m = PowerMeter(**kw).start()
    time.sleep(seconds)
    r = m.stop()
    return {"gpu_idle_w": r["gpu_avg_w"],
            "cpu_idle_w": (r["cpu_energy_j"] / r["duration_s"]) if r["cpu_energy_j"] is not None else None,
            "gpu_idle_mem_mib": r["gpu_peak_mem_mib"]}


def gpu_info(gpu_index=0):
    """GPU name, driver, VRAM and power limits (laptop TGP varies by model: record it)."""
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--id={gpu_index}",
             "--query-gpu=name,driver_version,memory.total,power.limit,power.max_limit,clocks.max.sm",
             "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout.strip()
        keys = ["name", "driver", "mem_total_mib", "power_limit_w", "power_max_limit_w", "max_sm_clock_mhz"]
        return dict(zip(keys, [x.strip() for x in out.split(",")]))
    except Exception:
        return None
