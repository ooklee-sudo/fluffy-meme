"""Print the tag structure of the first application in a USPTO weekly file (a few KB of text).

    python xml_skeleton.py ipa261008.zip
Paste the output into the chat. Text is cut to 40 characters; repeated sibling tags are collapsed.
"""
import io, re, sys, zipfile
import xml.etree.ElementTree as ET

src = sys.argv[1]
z = zipfile.ZipFile(src)
name = [n for n in z.namelist() if n.lower().endswith((".xml", ".txt"))][0]
print("zip members:", z.namelist()[:5])
head = io.TextIOWrapper(z.open(name), encoding="utf-8", errors="replace").read(3_000_000)
parts = re.split(r"(?=<\?xml)", head)
doc = next(p for p in parts[1:] if "</us-patent-application>" in p)
print("first doctype line:", re.findall(r"<!DOCTYPE[^>]*", doc)[:1])
doc = re.sub(r"<!DOCTYPE[^>]*(\[[^\]]*\])?[^>]*>", "", doc, count=1)
doc = re.sub(r"^<\?xml[^>]*\?>", "", doc.lstrip())
root = ET.fromstring(doc)


def show(el, depth=0, limit=2):
    attrs = " ".join(f'{k}="{v[:15]}"' for k, v in list(el.attrib.items())[:3])
    txt = (el.text or "").strip().replace("\n", " ")[:40]
    print("  " * depth + f"<{el.tag}{' ' + attrs if attrs else ''}>" + (f" {txt}" if txt else ""))
    if el.tag in ("description", "claims", "abstract") and depth > 3:
        return
    seen = {}
    for c in el:
        seen[c.tag] = seen.get(c.tag, 0) + 1
        if seen[c.tag] <= limit:
            show(c, depth + 1, limit)
        elif seen[c.tag] == limit + 1:
            print("  " * (depth + 1) + f"... more <{c.tag}>")


show(root)
