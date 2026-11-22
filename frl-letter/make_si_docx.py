"""Build si.docx from si.tex and add the S-prefixed numbers that pandoc drops."""
import subprocess
import docx

subprocess.run(["pandoc", "si.tex", "--citeproc", "--bibliography=references.bib",
                "--toc", "-o", "si.docx"], check=True)
d = docx.Document("si.docx")
sec = sub = tab = 0
for p in d.paragraphs:
    style = p.style.name
    if not p.runs:
        continue
    if style == "Heading 1" and p.text.strip() not in ("References", "Contents"):
        sec += 1
        sub = 0
        p.runs[0].text = f"S{sec} " + p.runs[0].text
    elif style == "Heading 2":
        sub += 1
        p.runs[0].text = f"S{sec}.{sub} " + p.runs[0].text
    elif style == "Table Caption":
        tab += 1
        p.runs[0].text = f"Table S{tab}. " + p.runs[0].text
d.save("si.docx")
print(f"{sec} sections, {tab} tables")
