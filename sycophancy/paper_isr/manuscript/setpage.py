"""Fix US Letter pages with 1-inch margins and add page numbers (ISR format) in a pandoc-made .docx."""
import re, sys, zipfile
SECT = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooterPg"/>'
        '<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" '
        'w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/>'
          '</w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/>'
          '</w:r></w:p></w:ftr>')
for path in sys.argv[1:]:
    z = zipfile.ZipFile(path); files = {n: z.read(n) for n in z.namelist()}; z.close()
    doc = files["word/document.xml"].decode()
    doc = re.sub(r"<w:sectPr.*?</w:sectPr>", "", doc, flags=re.S)
    doc = doc.replace("</w:body>", SECT + "</w:body>")
    files["word/document.xml"] = doc.encode()
    files["word/footer_pg.xml"] = FOOTER.encode()
    rels = files["word/_rels/document.xml.rels"].decode()
    if "rIdFooterPg" not in rels:
        rels = rels.replace("</Relationships>", '<Relationship Id="rIdFooterPg" Type="http://schemas.openxmlformats.org/'
                            'officeDocument/2006/relationships/footer" Target="footer_pg.xml"/></Relationships>')
    files["word/_rels/document.xml.rels"] = rels.encode()
    ct = files["[Content_Types].xml"].decode()
    if "footer_pg.xml" not in ct:
        ct = ct.replace("</Types>", '<Override PartName="/word/footer_pg.xml" ContentType="application/'
                        'vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
    files["[Content_Types].xml"] = ct.encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for n, d in files.items():
            out.writestr(n, d)
