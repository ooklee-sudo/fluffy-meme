#!/bin/bash
# Two-pass build of the Web Appendix PDF with a table of contents carrying page numbers. Usage: make_webappendix.sh <data_dir> <out_dir>
set -e
DATA="$1"; OUT="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"; mkdir -p "$OUT"; export TOC="$OUT/toc.json"; rm -f "$TOC"
python3 "$HERE/build_webappendix.py" "$DATA" "$OUT/Web_Appendix.docx" > /dev/null
soffice --headless --convert-to pdf --outdir "$OUT" "$OUT/Web_Appendix.docx" > /dev/null 2>&1
python3 - "$OUT" <<'PY'
import sys, json, subprocess, re
out = sys.argv[1]; n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', out + '/Web_Appendix.pdf'], capture_output=True, text=True).stdout).group(1))
secs = ['Web Appendix A: Study Inventory and Compute', 'Web Appendix B: Materials', 'Web Appendix C: Preregistrations and Deviation Log', 'Web Appendix D: Complete Results', 'Web Appendix E: Data Quality, Exclusions, and Known Issues', 'Web Appendix F: Code, Data, and Disclosures']
pages = {}
for p in range(2, n + 1):
    t = ' '.join(subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), out + '/Web_Appendix.pdf', '-'], capture_output=True, text=True).stdout.split())
    for s in secs:
        if s not in pages and t.startswith(s.split(':')[0]) and s.split(': ')[1][:25] in t[:200]: pages[s] = p
json.dump(pages, open(out + '/toc.json', 'w')); print(pages)
PY
python3 "$HERE/build_webappendix.py" "$DATA" "$OUT/Web_Appendix.docx" > /dev/null
soffice --headless --convert-to pdf --outdir "$OUT" "$OUT/Web_Appendix.docx" > /dev/null 2>&1
echo built "$OUT/Web_Appendix.pdf"
