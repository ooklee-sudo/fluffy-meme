import csv, gzip, os, tempfile, zipfile
import xml_to_tsv as x

def doc(num, filing, org, ctry, agent, n_par):
    agents = f'<agents><agent rep-type="attorney"><addressbook><orgname>{agent}</orgname></addressbook></agent></agents>' if agent else ""
    paras = "".join(f'<p id="p-{i:04d}" num="{i:04d}">The device {i} comprises a housing and a sensor coupled to the housing &amp; a processor. ' * 1 + "More text here. " * 12 + "</p>" for i in range(n_par))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE us-patent-application SYSTEM "us-patent-application-v46-2022-02-17.dtd" [ ]>
<us-patent-application lang="EN" dtd-version="v4.6 2022-02-17" file="US{num}A1.XML" status="PRODUCTION" id="us-patent-application" country="US" date-publ="20260101">
<us-bibliographic-data-application lang="EN" country="US">
<publication-reference><document-id><country>US</country><doc-number>{num}</doc-number><kind>A1</kind><date>20260101</date></document-id></publication-reference>
<application-reference appl-type="utility"><document-id><country>US</country><doc-number>18123456</doc-number><date>{filing}</date></document-id></application-reference>
<classifications-cpc><main-cpc><classification-cpc><section>G</section><class>06</class><subclass>N</subclass></classification-cpc></main-cpc></classifications-cpc>
<invention-title id="T1">A DEVICE</invention-title>
<us-parties><us-applicants><us-applicant sequence="00" app-type="applicant"><addressbook><orgname>{org}</orgname><address><city>X</city><country>{ctry}</country></address></addressbook></us-applicant></us-applicants>
<inventors><inventor sequence="00"><addressbook><last-name>Kim</last-name><first-name>A</first-name><address><country>{ctry}</country></address></addressbook></inventor></inventors>{agents}</us-parties>
</us-bibliographic-data-application>
<description id="description"><heading>BACKGROUND</heading>{paras}<tables><table>junk</table></tables></description>
</us-patent-application>
"""
d = tempfile.mkdtemp()
xml = "".join(doc(f"2026{i:07d}", "20250301", "Acme Corp", "KR" if i % 2 else "US", "Law LLP", 20) for i in range(30))
xml += doc("20269999999", "20250301", "Solo", "US", "", 20)   # an application without agents must still parse
p = os.path.join(d, "ipa260101.xml")
open(p, "w").write(xml + "<?xml version=\"1.0\"?>\n<broken><a></broken>\n")
with zipfile.ZipFile(p.replace(".xml", ".zip"), "w") as z: z.write(p, "ipa260101.xml")
out = os.path.join(d, "o.tsv.gz")
x.main([p.replace(".xml", ".zip"), out, "--n", "10"])
rows = list(csv.DictReader(gzip.open(out, "rt"), delimiter="\t"))
assert len(rows) == 10 and rows[0]["filing_date"] == "20250301" and rows[0]["agent_orgs"] == "Law LLP" and rows[0]["title"] == "A DEVICE"
assert {r["applicant_countries"] for r in rows} <= {"KR", "US"} and rows[0]["cpc_main"] == "G06N"
assert "junk" not in rows[0]["description_text"] and "&" in rows[0]["description_text"]
print("OK", {k: rows[0][k] for k in ("pgpub_id", "pub_date", "applicant_orgs", "agent_orgs", "cpc_main")})
