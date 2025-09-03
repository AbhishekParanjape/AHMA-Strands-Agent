from PyPDF2 import PdfReader
from pprint import pprint

def dump_acroform_fields(pdf_path):
    r = PdfReader(pdf_path)
    fields = r.get_fields() or {}
    out = []
    for name, fdict in fields.items():
        ft = (fdict.get("/FT") or fdict.get("FT"))
        v  = (fdict.get("/V")  or fdict.get("V"))
        out.append({
            "pdf_field_name": name,
            "field_type": str(ft),
            "value": v if not hasattr(v, "get_object") else v.get_object(),
        })
    return out

items = dump_acroform_fields("Medical Accident Living TPD claim form (Dec2024) (1).pdf")
pprint(items)