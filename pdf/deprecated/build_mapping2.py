import argparse
import json
from typing import Dict, Any
import PyPDF2
import re

# Simple noise detection
def is_noise(name: str) -> bool:
    if not name:
        return True
    low = str(name).lower()
    return bool(
        re.match(r"^check\s*box\d*$", low)   # Check BoxNN
        or re.match(r"^undefined[_\s]*\d*$", low)  
        or re.match(r"^text[_\s]*\d*$", low)# Undefined_NN
        or low in ("check box", "undefined", "text")
    )

def extract_fields(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Return mapping:
      field_name -> {
        "value": str or None,
        "rect": [x1, y1, x2, y2] or None,
        "page": int or None,
        "extraction_method": "annotation_widget" | "get_form_text_fields" | "acroform_fallback"
      }
    """
    out: Dict[str, Dict[str, Any]] = {}
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)

        # --- Pass 1: Annotations (widgets) ---
        for page_idx, page in enumerate(reader.pages):
            if "/Annots" not in page:
                continue
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                if annot.get("/Subtype") != "/Widget":
                    continue

                # Name
                name = None
                if "/T" in annot:
                    name = str(annot["/T"])
                elif "/Parent" in annot and "/T" in annot["/Parent"].get_object():
                    name = str(annot["/Parent"].get_object()["/T"])
                if not name or is_noise(name):
                    continue

                rect = [float(x) for x in annot.get("/Rect", [])] if "/Rect" in annot else None
                value = str(annot["/V"]) if "/V" in annot else None

                if name not in out:
                    out[name] = {
                        "value": value,
                        "rect": rect,
                        "page": page_idx,
                        "extraction_method": "annotation_widget",
                    }
                else:
                    if out[name].get("rect") is None and rect:
                        out[name]["rect"] = rect
                    if out[name].get("page") is None:
                        out[name]["page"] = page_idx
                    if not out[name].get("value") and value:
                        out[name]["value"] = value

        # --- Pass 2: PyPDF2 text fields ---
        try:
            text_fields = reader.get_form_text_fields() or {}
        except Exception:
            text_fields = {}

        for name, value in text_fields.items():
            if is_noise(name):
                continue
            if name not in out:
                out[name] = {
                    "value": value if value else None,
                    "rect": None,
                    "page": None,
                    "extraction_method": "get_form_text_fields",
                }
            else:
                if not out[name].get("value") and value:
                    out[name]["value"] = value

        # --- Pass 3: AcroForm fallback ---
        try:
            acroform = reader.trailer["/Root"].get("/AcroForm")
            if acroform and "/Fields" in acroform:
                for field_ref in acroform["/Fields"]:
                    field = field_ref.get_object()
                    name = field.get("/T")
                    if not name:
                        continue
                    name = str(name)
                    if is_noise(name):
                        continue

                    value = str(field.get("/V")) if field.get("/V") else None
                    rect = [float(x) for x in field.get("/Rect", [])] if "/Rect" in field else None

                    if name not in out:
                        out[name] = {
                            "value": value,
                            "rect": rect,
                            "page": None,
                            "extraction_method": "acroform_fallback",
                        }
                    else:
                        if not out[name].get("value") and value:
                            out[name]["value"] = value
                        if out[name].get("rect") is None and rect:
                            out[name]["rect"] = rect
        except Exception:
            pass

    return out


def main():
    ap = argparse.ArgumentParser(description="Extract concise field map from a PDF AcroForm.")
    ap.add_argument("--pdf", required=True, help="Path to PDF")
    ap.add_argument("--out", help="Output JSON path (default: <pdf>.json)")
    args = ap.parse_args()

    out_path = args.out or f"{args.pdf}.json"
    result = extract_fields(args.pdf)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path} with {len(result)} fields (noise excluded).")


if __name__ == "__main__":
    main()
