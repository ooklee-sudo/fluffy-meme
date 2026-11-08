"""Build the anonymous reproduction package: python release/build_zip.py (from the sycophancy folder)."""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
NAME = "room-to-reconsider-code"
FILES = [(os.path.join(SRC, f), f) for f in
         ("syco.py", "run_challenge.py", "analyze.py", "geometry.py", "steer.py", "make_figures.py")]
FILES += [(os.path.join(HERE, f), f) for f in ("README.md", "reproduce.sh", "requirements.txt", "LICENSE")]

out = os.path.join(HERE, NAME + ".zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for path, arc in FILES:
        info = zipfile.ZipInfo(f"{NAME}/{arc}", date_time=(2026, 1, 1, 0, 0, 0))  # no local timestamps
        info.external_attr = (0o755 if arc.endswith(".sh") else 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        with open(path, "rb") as f:
            z.writestr(info, f.read())
print(f"wrote {out}")
