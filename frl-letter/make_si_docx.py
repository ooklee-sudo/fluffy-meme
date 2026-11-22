"""Build si.docx from si.tex and add the appendix numbers (A, A.1, Table A.1) that pandoc drops."""
import subprocess
import docx

subprocess.run(["pandoc", "si.tex", "--citeproc", "--bibliography=references.bib",
                "--toc", "--csl=styles/elsevier-harvard.csl", "-o", "Online_Appendix.docx"], check=True)
d = docx.Document("Online_Appendix.docx")
sec = sub = tab = 0
letters = "ABCDEFGHIJ"
for p in d.paragraphs:
    style = p.style.name
    if not p.runs:
        continue
    if style == "Heading 1" and p.text.strip() not in ("References", "Contents"):
        sec += 1
        sub = tab = 0
        p.runs[0].text = f"Appendix {letters[sec - 1]}. " + p.runs[0].text
    elif style == "Heading 2":
        sub += 1
        p.runs[0].text = f"{letters[sec - 1]}.{sub} " + p.runs[0].text
    elif style == "Table Caption":
        tab += 1
        p.runs[0].text = f"Table {letters[sec - 1]}.{tab}. " + p.runs[0].text
d.save("Online_Appendix.docx")
print(f"{sec} appendices")
