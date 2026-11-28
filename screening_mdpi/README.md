# MDPI Electronics conversion script

Converts the IEEE TAI manuscript of the detector-ensemble screening paper (branch
`claude/ecstatic-fermi-i6ec13`, `nmi_screening/TAI_Manuscript.docx`) to the MDPI Electronics Word layout.
The manuscript files themselves are not kept here (unpublished paper, public repository).

```bash
python build_mdpi.py TAI_Manuscript.docx <mdpi_template_based.docx> Electronics_Manuscript.docx "Department ..., University, City; email"
```
