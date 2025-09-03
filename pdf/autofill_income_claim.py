#!/usr/bin/env python3
"""
Autofill "Medical/Accident/Living/Total and Permanent Disability Claim Form" (Income Insurance)
- Detect form type (AcroForm vs flat)
- Map canonical fields -> PDF field names (template-specific mapper)
- Resolve values from (DB -> rules/defaults -> RAG hook)
- Validate + log provenance
- Render (AcroForm write + appearance streams; fallback overlay)
- Optionally emit XFDF

Usage:
  python autofill_income_claim.py \
    --pdf "Medical Accident Living TPD claim form (Dec2024) (1).pdf" \
    --out filled.pdf \
    --xfdf out.xfdf \
    --data example_data.json \
    --map field_mapping_income_claim.json

Requires: PyPDF2>=3.0.0  reportlab  (install with: pip install PyPDF2 reportlab)
"""

import argparse, json, sys, io, datetime
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List

# Lazy imports so script can still show help without deps installed
def _lazy_imports():
    global PdfReader, PdfWriter, NameObject, BooleanObject
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from PyPDF2.generic import NameObject, BooleanObject
    except Exception as e:
        print("Please install PyPDF2: pip install PyPDF2", file=sys.stderr)
        raise

# --- Canonical schema (you can extend freely) ---
CANONICAL_FIELDS = [
    "insured_full_name",
    "insured_nric",
    "insured_gender",
    "insured_relationship_to_policyholder",
    "insured_occupation",
    "insured_employment_status",
    "insured_dob_ddmmyyyy",
    "employer_name_address",
    "employment_from_ddmmyyyy",
    "employment_to_ddmmyyyy",
    "duties_at_work",
    "insured_email",
    "policy_numbers",
    "plan_type",
    "claim_number",
    "claim_type_individual",
    "claim_type_incomeshield",
    "claim_type_affinity",
    "claim_type_mhs",
    "illness_or_accident",
    "diagnosis",
    "symptom_start_ddmmyyyy",
    "symptom_description",
    "family_history_yesno",
    "doctor_current_name_address",
    "hospitalisation_rows",
    "surgery_rows",
    "other_insurance_rows",
    "payment_method",
    "payee_bank_name",
    "payee_bank_account_number",
]

# --- Provenance + confidence container ---
@dataclass
class ValueWithProvenance:
    value: Any
    source: str   # 'db' | 'rule' | 'rag' | 'user'
    confidence: float  # 0..1

# --- Simple resolver chain (db -> rules -> rag) stubs ---
def resolve_value(key: str, supplied: Dict[str, Any], db: Dict[str, Any]) -> Optional[ValueWithProvenance]:
    # 1) DB lookup (stub)
    if key in db:
        return ValueWithProvenance(db[key], "db", 0.95)
    # 2) Rules/defaults (very basic demo rules)
    if key == "insured_gender" and "insured_nric" in supplied:
        return None
    # 3) RAG hook (stubbed: only used if user didn't supply and DB didn't have it)
    if key not in supplied:
        return None
    # 4) User-supplied
    return ValueWithProvenance(supplied[key], "user", 0.99)

# --- Validators (add as needed) ---
def validate_date_ddmmyyyy(s: str) -> bool:
    try:
        datetime.datetime.strptime(s, "%d/%m/%Y")
        return True
    except Exception:
        return False

def validate_email(s: str) -> bool:
    return "@" in s and "." in s

# --- Mapper + filler ---
def load_mapping(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def set_need_appearances(writer):
    # Ask viewer to regenerate appearances (useful for Acrobat/Preview)
    if "/AcroForm" in writer._root_object:
        acro = writer._root_object["/AcroForm"]
        acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})

def write_acroform(pdf_in: str, pdf_out: str, field_values: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Return (success, logs)."""
    _lazy_imports()
    logs = []
    try:
        reader = PdfReader(pdf_in)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        # Copy AcroForm if present (ensure objects belong to this writer)
        if "/AcroForm" in reader.trailer["/Root"]:
            acro_obj = writer._add_object(reader.trailer["/Root"]["/AcroForm"])
            writer._root_object.update({NameObject("/AcroForm"): acro_obj})
        else:
            logs.append("No AcroForm detected; will need overlay fallback.")
            # Still write out; caller will overlay later
            with open(pdf_out, "wb") as f:
                writer.write(f)
            return False, logs

        # Update fields
        form = reader.get_fields() or {}
        for pdf_key, v in field_values.items():
            try:
                if isinstance(v, bool):
                    v = "Yes" if v else "Off"
                for page in writer.pages:
                    writer.update_page_form_field_values(page, {pdf_key: v})
                logs.append(f"Set field '{pdf_key}' -> {v!r}")
            except Exception as e:
                logs.append(f"Could not set field '{pdf_key}': {e}")

        set_need_appearances(writer)
        with open(pdf_out, "wb") as f:
            writer.write(f)
        return True, logs
    except Exception as e:
        logs.append(f"AcroForm write error: {e}")
        return False, logs

# --- Simple overlay (uses reportlab) ---
def overlay_write(pdf_in: str, pdf_out: str, overlay_instructions: List[Tuple[int, float, float, str]]):
    """
    overlay_instructions: list of (page_index, x, y, text) to draw at absolute coords (points)
    NOTE: Coordinates are template-specific (measure once with a PDF tool).
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from PyPDF2 import PdfReader, PdfWriter
        from PyPDF2.pdf import PageObject  # type: ignore
    except Exception as e:
        print("Overlay requires reportlab + PyPDF2. pip install reportlab PyPDF2", file=sys.stderr)
        raise

    base = PdfReader(pdf_in)
    writer = PdfWriter()

    # Per-page overlays
    buffers: Dict[int, io.BytesIO] = {}
    canvases = {}

    for (p, x, y, text) in overlay_instructions:
        if p not in buffers:
            buffers[p] = io.BytesIO()
            c = canvas.Canvas(buffers[p], pagesize=(base.pages[p].mediabox.width, base.pages[p].mediabox.height))
            c.setFont("Helvetica", 10)
            canvases[p] = c
        canvases[p].drawString(x, y, text)

    for p, c in canvases.items():
        c.save()

    for i, page in enumerate(base.pages):
        if i in buffers:
            overlay_pdf = PdfReader(buffers[i])
            page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    with open(pdf_out, "wb") as f:
        writer.write(f)

# --- XFDF emitter ---
def emit_xfdf(xfdf_path: str, field_map: Dict[str, Any], resolved: Dict[str, Any]):
    def esc(s: str) -> str:
        return (s.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))
    items = []
    for canonical, pdf_name in field_map["pdf_fields"].items():
        if canonical in resolved:
            val = resolved[canonical]["value"]
            if isinstance(val, bool):
                val = "Yes" if val else "Off"
            items.append(f'<field name="{esc(pdf_name)}"><value>{esc(str(val))}</value></field>')
    xfdf = """<?xml version="1.0" encoding="UTF-8"?>
<xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
  <fields>
    {items}
  </fields>
  <f href=""/>
</xfdf>""".replace("{items}", "".join(items))
    with open(xfdf_path, "w", encoding="utf-8") as f:
        f.write(xfdf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data", required=True, help="JSON of canonical values (user/db)")
    ap.add_argument("--map", required=True, help="JSON mapping file for this template")
    ap.add_argument("--xfdf", default=None)
    args = ap.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        user_data = json.load(f)
    mapping = load_mapping(args.map)

    db_stub = {}
    resolved: Dict[str, Dict[str, Any]] = {}
    for key in CANONICAL_FIELDS:
        vw = resolve_value(key, user_data, db_stub)
        if vw is not None:
            if key.endswith("_ddmmyyyy") and isinstance(vw.value, str) and not validate_date_ddmmyyyy(vw.value):
                print(f"[WARN] {key} invalid date: {vw.value}", file=sys.stderr)
            if key.endswith("_email") and isinstance(vw.value, str) and not validate_email(vw.value):
                print(f"[WARN] {key} invalid email: {vw.value}", file=sys.stderr)
            resolved[key] = {"value": vw.value, "source": vw.source, "confidence": vw.confidence}

    to_pdf: Dict[str, Any] = {}
    for canonical, pdf_name in mapping.get("pdf_fields", {}).items():
        if canonical in resolved:
            to_pdf[pdf_name] = resolved[canonical]["value"]

    def set_checkbox_group(group_map_key: str, selected_values: List[str]):
        checkbox_map = mapping.get(group_map_key, {})
        for label, pdf_field in checkbox_map.items():
            to_pdf[pdf_field] = "Yes" if label in selected_values else "Off"

    set_checkbox_group("checkboxes_individual_claim_type", user_data.get("claim_type_individual", []))
    set_checkbox_group("checkboxes_incomeshield_claim_type", user_data.get("claim_type_incomeshield", []))
    set_checkbox_group("checkboxes_affinity_claim_type", user_data.get("claim_type_affinity", []))
    set_checkbox_group("checkboxes_mhs_claim_type", user_data.get("claim_type_mhs", []))

    gender_map = mapping.get("checkboxes_gender", {})
    if "insured_gender" in user_data:
        for g, pdf_field in gender_map.items():
            to_pdf[pdf_field] = "Yes" if g.lower() == str(user_data["insured_gender"]).lower() else "Off"

    emp_map = mapping.get("checkboxes_employment_status", {})
    if "insured_employment_status" in user_data:
        for status, pdf_field in emp_map.items():
            to_pdf[pdf_field] = "Yes" if status.lower() == str(user_data["insured_employment_status"]).lower() else "Off"

    ok, logs = write_acroform(args.pdf, args.out, to_pdf)
    for line in logs:
        print(line)

    if args.xfdf:
        emit_xfdf(args.xfdf, mapping, resolved)

    if not ok:
        print("[INFO] Falling back to overlay—measure coordinates and update the overlay list in code.", file=sys.stderr)

if __name__ == "__main__":
    main()
