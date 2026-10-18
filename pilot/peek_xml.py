"""Cut the first few MB of the XML inside a USPTO weekly file so its structure can be checked.

    python peek_xml.py ipa261008.zip ipa_peek.xml.gz [--mb 4]
"""
import gzip, sys, zipfile

src, dst = sys.argv[1], sys.argv[2]
mb = float(sys.argv[sys.argv.index("--mb") + 1]) if "--mb" in sys.argv else 4.0
z = zipfile.ZipFile(src)
name = [n for n in z.namelist() if n.lower().endswith((".xml", ".txt"))][0]
with z.open(name) as f, gzip.open(dst, "wb") as g:
    g.write(f.read(int(mb * 1_000_000)))
print("members:", z.namelist(), "| wrote", dst)
