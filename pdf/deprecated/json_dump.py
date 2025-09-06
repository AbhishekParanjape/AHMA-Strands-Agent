#!/usr/bin/env python3
import argparse, json
from typing import Any, Dict, Iterable, List, Optional, Union
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject, ArrayObject, DictionaryObject


def _resolve(obj):
    """Resolve a PyPDF2 object to its underlying value (recursively for one hop)."""
    try:
        return obj.get_object() if isinstance(obj, IndirectObject) else obj
    except Exception:
        return obj


def _iter_annots(page) -> Iterable[DictionaryObject]:
    """
    Yield widget annotations on a page, robust to /Annots being:
      - missing
      - an IndirectObject (ref to array)
      - an ArrayObject of refs/dicts
      - a single ref/dict (some malformed PDFs)
    """
    annots = page.get("/Annots")
    if not annots:
        return

    annots = _resolve(annots)

    # Normalize to a list of items (even if it's a single dict/ref)
    if isinstance(annots, ArrayObject):
        items = list(annots)
    elif isinstance(annots, (IndirectObject, DictionaryObject)):
        items = [annots]
    else:
        # Unknown structure; best effort: try to iterate or wrap
        try:
            items = list(annots)  # may raise
        except Exception:
            items = [annots]

    for item in items:
        annot = _resolve(item)
        if not isinstance(annot, DictionaryObject):
            continue
        if annot.get("/Subtype") != "/Widget":
            continue
        yield annot


def _str_or_none(pdf_obj: Any) -> Optional[str]:
    if pdf_obj is None:
        return None
    try:
        return str(pdf_obj)
    except Exception:
        # Fallback to repr if str fails
        return repr(pdf_obj)


def _float_list_or_none(pdf_obj: Any) -> Optional[List[float]]:
    if not pdf_obj:
        return None
    try:
        values = list(pdf_obj)
        return [float(x) for x in values]
    except Exception:
        return None


def extract_field_objects(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract widget/field objects per-page and dump raw keys.
    Keyed by /T (field name) if available, else 'unnamed_{page}_{idx}'.
    """
    out: Dict[str, Dict[str, Any]] = {}
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)

        for page_idx, page in enumerate(reader.pages):
            i = 0
            for annot in _iter_annots(page):
                i += 1

                # Field name (/T) might live on the widget or its /Parent
                field_name = None
                if annot.get("/T"):
                    field_name = _str_or_none(annot.get("/T"))
                else:
                    parent = annot.get("/Parent")
                    parent = _resolve(parent) if parent else None
                    if isinstance(parent, DictionaryObject) and parent.get("/T"):
                        field_name = _str_or_none(parent.get("/T"))
                if not field_name:
                    field_name = f"unnamed_{page_idx}_{i}"

                out[field_name] = {
                    "page": page_idx,
                    "rect": _float_list_or_none(annot.get("/Rect")),
                    "T": _str_or_none(annot.get("/T")),
                    "V": _str_or_none(annot.get("/V")),
                    "DV": _str_or_none(annot.get("/DV")),
                    "AS": _str_or_none(annot.get("/AS")),
                    "FT": _str_or_none(annot.get("/FT")),
                    "Ff": annot.get("/Ff"),
                    "raw_keys": [ _str_or_none(k) for k in annot.keys() ],
                }

    return out


def extract_acroform_hierarchy(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Dump /AcroForm /Fields hierarchy (parents + kids), which can reveal
    inherited /T, /FT, etc. Useful when widgets don’t carry all info.
    """
    rows: List[Dict[str, Any]] = []
    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        root = reader.trailer.get("/Root")
        acro = root.get("/AcroForm") if root else None
        if not acro:
            return rows
        acro = _resolve(acro)
        fields = acro.get("/Fields") if isinstance(acro, DictionaryObject) else None
        fields = _resolve(fields) if fields else None
        if not isinstance(fields, ArrayObject):
            return rows

        def walk(field_obj, path=""):
            fld = _resolve(field_obj)
            if not isinstance(fld, DictionaryObject):
                return
            name = _str_or_none(fld.get("/T"))
            full_path = f"{path}.{name}" if path and name else (name or path or "<no-name>")

            rows.append({
                "path": full_path,
                "T": name,
                "FT": _str_or_none(fld.get("/FT")),
                "V": _str_or_none(fld.get("/V")),
                "DV": _str_or_none(fld.get("/DV")),
                "Ff": fld.get("/Ff"),
                "Kids": len(_resolve(fld.get("/Kids"))) if _resolve(fld.get("/Kids")) else 0,
                "raw_keys": [ _str_or_none(k) for k in fld.keys() ],
            })

            kids = _resolve(fld.get("/Kids"))
            if isinstance(kids, ArrayObject):
                for k in kids:
                    walk(k, full_path)

        for fref in fields:
            walk(fref, "")

    return rows


def main():
    ap = argparse.ArgumentParser(description="Dump raw AcroForm field objects (/T, /V, /AS, /Rect, etc.) to JSON")
    ap.add_argument("--pdf", required=True, help="Input PDF with AcroForm fields")
    ap.add_argument("--out", required=True, help="Output JSON file for widget dump")
    ap.add_argument("--out_hierarchy", help="Optional JSON file for AcroForm hierarchy dump")
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
