# ISR-format build (economics framing)
Needs Node with `docx` (`npm install docx` in this folder). `node isr_econ.js ../ISR_AIreview_manuscript_v1.docx` builds the anonymous manuscript with the INFORMS-style citations and reference list; `lib.js` holds the layout (Times New Roman 12 pt, double spaced, 1-inch margins, page numbers, no author information).
The title page and cover letter are Word files built with python-docx and are edited in Word. Edit the manuscript text in `isr_econ.js`, not in the .docx.
