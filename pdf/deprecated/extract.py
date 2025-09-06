from PyPDF2 import PdfReader  # pip install pypdf
from pprint import pprint

pdf_path = "Medical Accident Living TPD claim form (Dec2024) (1).pdf"
r = PdfReader(pdf_path)
root = r.trailer["/Root"]

acro = root.get("/AcroForm")
xfa  = acro.get("/XFA") if acro else None

print("Has AcroForm? ", bool(acro))
print("Has XFA?      ", bool(xfa))
