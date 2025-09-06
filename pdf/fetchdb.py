#!/usr/bin/env python3
import argparse, json, re, sys
from typing import Any, Dict, Optional, Tuple
from difflib import get_close_matches

import boto3


# ----------------------------
# Helpers
# ----------------------------

def load_dump(path: str) -> Dict[str, Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

"""def s3_get_json(bucket: str, key: str) -> Dict[str, Any]:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. `pip install boto3`.")
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    # Try utf-8 then latin-1 fallback
    try:
        body = obj["Body"].read().decode("utf-8")
    except UnicodeDecodeError:
        body = obj["Body"].read().decode("latin-1")
    return json.loads(body)"""

def normalize_key(s: str) -> str:
    """Lowercase, remove non-alphanum, collapse spaces. Keeps letters+digits only."""
    s = s.strip().lower()
    s = re.sub(r"[\s_]+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return re.sub(r"\s+", " ", s)

def flatten_dict(d: Dict[str, Any], parent: str = "", sep: str = ".") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{parent}{sep}{k}" if parent else str(k)
        if isinstance(v, dict):
            out.update(flatten_dict(v, key, sep))
        else:
            out[key] = v
    return out

def truthy(v: Any) -> Optional[bool]:
    """Interpret a value as boolean if possible, else None."""
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1", "on", "checked"}:
        return True
    if s in {"false", "no", "n", "0", "off", "unchecked"}:
        return False
    return None

def is_checkbox(field: Dict[str, Any]) -> bool:
    """Detect checkbox: /FT == /Btn and not obviously a pushbutton."""
    ft = str(field.get("FT") or "").strip()
    if ft != "/Btn":
        return False
    # Optional: Use /Ff flags to filter pushbutton/radio, but many dumps won’t expose nicely.
    # For safety, treat /Btn as checkbox unless you know this form uses radios extensively.
    return True

def acro_checkbox_state(on_token: Optional[str], desired: bool) -> str:
    """
    Return the correct /AS or /V token for a checkbox:
      - Use the existing non-/Off token if present (e.g. '/Yes', '/On', '/1')
      - Default to '/Yes' if unknown.
    """
    token = on_token if on_token and on_token != "/Off" else "/Yes"
    return token if desired else "/Off"

def best_match_key(field_name: str, norm_to_original: Dict[str, str]) -> Optional[str]:
    """Exact normalized match first, then fuzzy close match."""
    norm = normalize_key(field_name)
    if norm in norm_to_original:
        return norm_to_original[norm]
    
    # Try partial matching for complex field names
    candidates = list(norm_to_original.keys())
    
    # First try: find candidates that contain the field name as a substring
    for candidate in candidates:
        if norm in candidate or candidate in norm:
            return norm_to_original[candidate]
    
    # Second try: fuzzy matching with lower threshold
    hit = get_close_matches(norm, candidates, n=1, cutoff=0.7)
    if hit:
        return norm_to_original[hit[0]]
    
    return None


# ----------------------------
# Core logic
# ----------------------------

def build_values_from_s3(
    dump: Dict[str, Dict[str, Any]],
    patient_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Return a { field_title: value } mapping:
      - Text/choice fields: string value
      - Checkboxes: '/Yes' or '/Off' (AcroForm checkbox states)
    """
    flat = flatten_dict(patient_data)
    # Build normalized lookup
    norm_to_original: Dict[str, str] = {}
    for k in flat:
        norm_to_original[normalize_key(k)] = k

    out: Dict[str, Any] = {}
    matched_count = 0
    total_fields = len(dump)

    for key, field in dump.items():
        # Use /T if available; otherwise the dict key is the best we have
        title = field.get("T") or key
        if not title:
            continue

        patient_key = best_match_key(title, norm_to_original)
        if not patient_key:
            # No match: skip
            print(f"No match for field: '{title}'")
            continue

        matched_count += 1
        src_value = flat[patient_key]
        print(f"Matched '{title}' -> '{patient_key}' = {src_value}")
        
        # Decide how to encode
        if is_checkbox(field):
            bool_val = truthy(src_value)
            if bool_val is None:
                # If the patient source is not interpretable as boolean,
                # prefer not to set it rather than guess.
                print(f"  Skipping checkbox '{title}' - cannot interpret value as boolean")
                continue
            # Discover ON token from existing AS if any
            on_token = field.get("AS")
            checkbox_value = acro_checkbox_state(on_token, bool_val)
            out[title] = checkbox_value
            print(f"  Checkbox '{title}' -> {checkbox_value}")
        else:
            # Text/choice/signature/radio parent: just coerce to str
            text_value = "" if src_value is None else str(src_value)
            out[title] = text_value
            print(f"  Text field '{title}' -> '{text_value}'")

    print(f"\nMatched {matched_count}/{total_fields} fields")
    return out


# ----------------------------
# CLI
# ----------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Fill AcroForm values from example data JSON (checkboxes -> /Yes|/Off)."
    )
    ap.add_argument("--dump", required=True, help="Path to dump JSON (from your dump script)")
    ap.add_argument("--example-data", default="example_data.json", help="Path to example data JSON")
    ap.add_argument("--out", required=True, help="Output values JSON (for your PDF writer)")
    args = ap.parse_args()

    try:
        dump = load_dump(args.dump)
    except Exception as e:
        print(f"ERROR: failed to load dump JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.example_data, "r", encoding="utf-8") as f:
            patient = json.load(f)
    except Exception as e:
        print(f"ERROR: failed to load example data JSON: {e}", file=sys.stderr)
        sys.exit(2)

    values = build_values_from_s3(dump, patient)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(values)} field values to {args.out}")


if __name__ == "__main__":
    main()
