import argparse, json
from typing import Any, Dict, Iterable, List, Optional
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject, ArrayObject, DictionaryObject


def _resolve(obj):
    """Resolve a PyPDF2 object to its underlying value (one hop)."""
    try:
        return obj.get_object() if isinstance(obj, IndirectObject) else obj
    except Exception:
        return obj


def _iter_annots(page) -> Iterable[DictionaryObject]:
    """Yield widget annotations from a page."""
    annots = page.get("/Annots")
    if not annots:
        return
    annots = _resolve(annots)

    if isinstance(annots, ArrayObject):
        items = list(annots)
    elif isinstance(annots, (IndirectObject, DictionaryObject)):
        items = [annots]
    else:
        try:
            items = list(annots)
        except Exception:
            items = [annots]

    for item in items:
        annot = _resolve(item)
        if isinstance(annot, DictionaryObject) and annot.get("/Subtype") == "/Widget":
            yield annot


def _str_or_none(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    try:
        return str(obj)
    except Exception:
        return None


def _float_list_or_none(obj: Any) -> Optional[List[float]]:
    if not obj:
        return None
    try:
        return [float(x) for x in obj]
    except Exception:
        return None


def _is_noise(name: Optional[str]) -> bool:
    """Filter out checkboxes, undefined, or noise names."""
    if not name:
        return True
    lname = name.lower()
    if "check box" in lname or "checkbox" in lname:
        return True
    if "undefined" in lname:
        return True
    return False


def extract_field_objects(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract fields keyed by /T (field name).
    Skip checkboxes and undefined names.
    """
    out: Dict[str, Dict[str, Any]] = {}
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)

        for page_idx, page in enumerate(reader.pages):
            for i, annot in enumerate(_iter_annots(page), start=1):
                # field name
                field_name = None
                if annot.get("/T"):
                    field_name = _str_or_none(annot.get("/T"))
                else:
                    parent = _resolve(annot.get("/Parent"))
                    if isinstance(parent, DictionaryObject) and parent.get("/T"):
                        field_name = _str_or_none(parent.get("/T"))
                if not field_name:
                    field_name = f"unnamed_{page_idx}_{i}"

                if _is_noise(field_name):
                    continue

                out[field_name] = {
                    "page": page_idx,
                    "rect": _float_list_or_none(annot.get("/Rect")),
                    "T": _str_or_none(annot.get("/T")),
                    "V": _str_or_none(annot.get("/V")),
                    "DV": _str_or_none(annot.get("/DV")),
                    "AS": _str_or_none(annot.get("/AS")),
                    "FT": _str_or_none(annot.get("/FT")),
                    "Ff": annot.get("/Ff"),
                }

    return out


def extract_acroform_hierarchy(pdf_path: str) -> List[Dict[str, Any]]:
    """Dump /AcroForm /Fields hierarchy (parents + kids)."""
    rows: List[Dict[str, Any]] = []
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        root = reader.trailer.get("/Root")
        acro = _resolve(root.get("/AcroForm")) if root else None
        fields = _resolve(acro.get("/Fields")) if isinstance(acro, DictionaryObject) else None
        if not isinstance(fields, ArrayObject):
            return rows

        def walk(field_obj, path=""):
            fld = _resolve(field_obj)
            if not isinstance(fld, DictionaryObject):
                return
            name = _str_or_none(fld.get("/T"))
            full_path = f"{path}.{name}" if path and name else (name or path or "<no-name>")

            if not _is_noise(name):
                rows.append({
                    "path": full_path,
                    "T": name,
                    "FT": _str_or_none(fld.get("/FT")),
                    "V": _str_or_none(fld.get("/V")),
                    "DV": _str_or_none(fld.get("/DV")),
                    "Ff": fld.get("/Ff"),
                    "Kids": len(_resolve(fld.get("/Kids"))) if _resolve(fld.get("/Kids")) else 0,
                })

            kids = _resolve(fld.get("/Kids"))
            if isinstance(kids, ArrayObject):
                for k in kids:
                    walk(k, full_path)

        for fref in fields:
            walk(fref, "")

    return rows


def main():
    ap = argparse.ArgumentParser(description="Dump AcroForm fields to JSON (cleaned)")
    ap.add_argument("--pdf", required=True, help="Input PDF with AcroForm fields")
    ap.add_argument("--out", required=True, help="Output JSON file for widget dump")
    ap.add_argument("--out-hierarchy", help="Optional JSON file for AcroForm hierarchy dump")
    args = ap.parse_args()

    widgets = extract_field_objects(args.pdf)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(widgets, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(widgets)} widget entries to {args.out}")

    if args.out_hierarchy:
        hierarchy = extract_acroform_hierarchy(args.pdf)
        with open(args.out_hierarchy, "w", encoding="utf-8") as f:
            json.dump(hierarchy, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(hierarchy)} hierarchy rows to {args.out_hierarchy}")


if __name__ == "__main__":
    main()
