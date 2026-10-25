"""Stream the Public Jira Dataset mongodump (inside the Zenodo zip) and extract a compact bug table.

Zenodo record 15719919 ("The Public Jira Dataset", Montgomery, Lueders & Maalej, CC-BY-4.0).
The zip holds one gzip-compressed mongodump archive (~60 GB expanded). We do NOT restore MongoDB: the archive is
parsed as a stream (magic, prelude, then [collection header][BSON docs]...[terminator] blocks; up to 4 collections
interleaved) and only the wanted collections are decoded.

Output CSV (one row per bug-like issue): repo, project, key, type, priority, created, resolutiondate, resolution,
affects (name|releaseDate;...), fixes (name|releaseDate;...)

Usage: python3 -I jira_extract_bugs.py <zip> <member.json> <out.csv> [collections comma-separated] [max_bytes_of_stream]
"""
import csv
import json
import struct
import sys
import time
import zlib
import bson

zip_path, member_json, out_csv = sys.argv[1:4]
WANT = set((sys.argv[4] if len(sys.argv) > 4 else "Apache,Qt,MongoDB,Sakai,Hyperledger,Spring").split(","))
LIMIT = int(sys.argv[5]) if len(sys.argv) > 5 else None


class Stream:
    """Decompress zip member (deflate) then gzip, exposing read(n)."""
    def __init__(self, path, mem):
        self.f = open(path, "rb")
        self.f.seek(mem["offset"])
        lh = self.f.read(30)
        nlen, elen = struct.unpack("<HH", lh[26:30])
        self.f.read(nlen + elen)
        self.remaining = mem["comp"]
        self.d1 = zlib.decompressobj(-15)
        self.d2 = zlib.decompressobj(31)
        self.buf = bytearray()
        self.total = 0
        self.eof = False

    def _fill(self):
        while not self.eof:
            n = min(8 << 20, self.remaining)
            raw = self.f.read(n) if n > 0 else b""
            self.remaining -= len(raw)
            if not raw:
                self.eof = True
                return
            out = self.d2.decompress(self.d1.decompress(raw))
            if out:
                self.buf += out
                return

    def read(self, n):
        while len(self.buf) < n and not self.eof:
            self._fill()
        out = bytes(self.buf[:n]); del self.buf[:n]; self.total += len(out)
        return out


def read_doc(s):
    h = s.read(4)
    if len(h) < 4:
        return "EOS"
    L = struct.unpack("<i", h)[0]
    if L == -1:
        return None
    return h + s.read(L - 4)


def names(lst):
    out = []
    for v in lst or []:
        if isinstance(v, dict):
            out.append(f"{v.get('name', '')}|{v.get('releaseDate', '')}")
    return ";".join(out)


mem = json.load(open(member_json))
s = Stream(zip_path, mem)
assert struct.unpack("<I", s.read(4))[0] == 0x8199E26D
read_doc(s)                                    # header
while read_doc(s) is not None:                 # prelude namespace docs until terminator
    pass
current, n_seen, n_kept, t0 = None, {}, {}, time.time()
with open(out_csv, "w", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["repo", "project", "key", "type", "priority", "created", "resolutiondate", "resolution", "affects", "fixes"])
    while True:
        if LIMIT and s.total > LIMIT:
            break
        raw = read_doc(s)
        if raw == "EOS":
            break
        if raw is None:                        # block terminator
            current = None
            continue
        if current is None:                    # collection header
            hdr = bson.decode(raw)
            current = (hdr.get("collection"), hdr.get("EOF", False))
            continue
        coll, is_eof = current
        if is_eof or coll not in WANT:
            continue
        n_seen[coll] = n_seen.get(coll, 0) + 1
        d = bson.decode(raw)
        fl = d.get("fields", {}) or {}
        itype = ((fl.get("issuetype") or {}).get("name") or "")
        if "bug" not in itype.lower() and "defect" not in itype.lower():
            continue
        key = d.get("key", "")
        w.writerow([coll, (fl.get("project") or {}).get("key", key.rsplit("-", 1)[0]), key, itype,
                    (fl.get("priority") or {}).get("name", ""), fl.get("created", ""), fl.get("resolutiondate", "") or "",
                    (fl.get("resolution") or {}).get("name", "") if isinstance(fl.get("resolution"), dict) else "",
                    names(fl.get("versions")), names(fl.get("fixVersions"))])
        n_kept[coll] = n_kept.get(coll, 0) + 1
        if sum(n_kept.values()) % 50000 == 0:
            print(f"{s.total/1e9:.1f} GB streamed, {time.time()-t0:.0f}s, seen {n_seen}, kept {n_kept}", flush=True)
print("done. streamed %.1f GB in %.0fs. seen %s kept %s" % (s.total / 1e9, time.time() - t0, n_seen, n_kept))
