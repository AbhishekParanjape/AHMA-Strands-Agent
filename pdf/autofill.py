#!/usr/bin/env python3
import argparse, json
from typing import Any, Dict

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, TextStringObject, BooleanObject, IndirectObject

# ---------- helpers ----------
def resolve(obj):
    """Follow .get_object() until it's not an IndirectObject."""
    while isinstance(obj, IndirectObject):
        obj = obj.get_object()
    return obj

TRUEY = {"yes", "true", "on", "1", 1, True}
FALSEY = {"no", "false", "off", "0", 0, False, None, ""}

def is_true_like(x: Any):
    if isinstance(x, str):
        s = x.strip().lower()
        if s in TRUEY: return True
        if s in FALSEY: return False
        if s.startswith("/") and s != "/off": return True
        if s == "/off": return False
        return None
    if x in TRUEY: return True
    if x in FALSEY: return False
    return None

def pick_checkbox_on_state(annot_dict) -> NameObject:
    ap = annot_dict.get("/AP")
    if ap:
        ap = resolve(ap)
        normal = ap.get("/N")
        if normal:
            normal = resolve(normal)
            for state in normal.keys():
                if str(state) != "/Off":
                    return NameObject(str(state))
    return NameObject("/Yes")

def load_values(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)
    out = {}
    for k, v in raw.items():
        out[k] = v.get("V") if isinstance(v, dict) and "V" in v else v
    return out

# ---------- main fill ----------
def fill_pdf_from_values(pdf_in: str, pdf_out: str, values: Dict[str, Any]) -> None:
    reader = PdfReader(pdf_in)
    writer = PdfWriter()

    # Resolve /AcroForm and set NeedAppearances
    acroform = reader.trailer["/Root"].get("/AcroForm")
    if acroform:
        acroform_obj = resolve(acroform)
        acroform_obj.update({NameObject("/NeedAppearances"): BooleanObject(True)})
        writer._root_object.update({NameObject("/AcroForm"): acroform_obj})

    for page in reader.pages:
        # Resolve /Annots — it can be an IndirectObject to an Array
        annots = page.get("/Annots")
        if annots:
            annots = resolve(annots)
            if isinstance(annots, list):
                for aref in annots:
                    annot = resolve(aref)
                    if annot.get("/Subtype") != "/Widget":
                        continue

                    # Field name may be on widget or its parent
                    name = None
                    if "/T" in annot:
                        name = str(annot["/T"])
                    elif "/Parent" in annot:
                        parent = resolve(annot["/Parent"])
                        if "/T" in parent:
                            name = str(parent["/T"])
                    if not name or name not in values:
                        continue

                    desired = values[name]

                    # Determine field type (prefer widget, else parent)
                    ft = annot.get("/FT")
                    if ft is None and "/Parent" in annot:
                        ft = resolve(annot["/Parent"]).get("/FT")
                    ft_str = str(ft) if ft else None

                    # /Btn = checkbox/radio
                    if ft_str == "/Btn":
                        truthy = is_true_like(desired)
                        if truthy is None:
                            s = str(desired).strip()
                            if s.startswith("/"):
                                on_state = NameObject(s)
                                annot.update({NameObject("/V"): on_state})
                                annot.update({NameObject("/AS"): on_state})
                            else:
                                annot.update({NameObject("/V"): NameObject("/Off")})
                                annot.update({NameObject("/AS"): NameObject("/Off")})
                        elif truthy:
                            on_state = pick_checkbox_on_state(annot)
                            annot.update({NameObject("/V"): on_state})
                            annot.update({NameObject("/AS"): on_state})
                        else:
                            annot.update({NameObject("/V"): NameObject("/Off")})
                            annot.update({NameObject("/AS"): NameObject("/Off")})

                    # /Tx (text) or unknown (some PDFs omit /FT on widget)
                    elif ft_str == "/Tx" or ft is None:
                        annot.update({NameObject("/V"): TextStringObject(str(desired))})

                    # /Ch (choice: dropdown/list)
                    elif ft_str == "/Ch":
                        annot.update({NameObject("/V"): TextStringObject(str(desired))})

                    # else ignore unsupported types

        writer.add_page(page)

    with open(pdf_out, "wb") as f:
        writer.write(f)

def main():
    ap = argparse.ArgumentParser(description="Fill PDF (AcroForm) from JSON")
    ap.add_argument("--pdf-in", required=True)
    ap.add_argument("--pdf-out", required=True)
    ap.add_argument("--values", required=True, help="JSON {name:value} or {name:{V:..}}")
    args = ap.parse_args()
    values = load_values(args.values)
    fill_pdf_from_values(args.pdf_in, args.pdf_out, values)
    print(f"Filled PDF written to {args.pdf_out}")

if __name__ == "__main__":
    main()

