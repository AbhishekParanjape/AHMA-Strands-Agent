
#!/usr/bin/env python3
"""
Build a template-specific JSON mapping from a PDF *or* from a pre-dumped
field list (list of {pdf_field_name, field_type, value}).

Usage:
  # From PDF (requires: pip install pypdf)
  python build_mapping.py --pdf "Medical Accident Living TPD claim form (Dec2024) (1).pdf" --out field_mapping.json

  # From a dump you already have (list[dict] in JSON):
  python build_mapping.py --dump fields_dump.json --out field_mapping.json

Heuristics baked-in for the Income Insurance "Medical/Accident/Living/TPD Claim" template:
- Claim Type buckets (Individual, IncomeShield, Affinity, MHS)
- Gender
- Employment status
- Payment method
- Confinement, A&E, referrals, surgery/overseas/treated-before toggles
- Signature and long free-text blocks

You can adapt the keyword lists below for other templates.
"""

import argparse, json, sys
import re
from typing import List, Dict, Any, Tuple

# -------------------- Helpers --------------------

def slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    s = re.sub(r'_+', '_', s)
    return s

def load_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        from PyPDF2 import PdfReader  # pip install pypdf
    except Exception as e:
        print("ERROR: 'pypdf' not installed. Install with: pip install pypdf", file=sys.stderr)
        raise
    r = PdfReader(pdf_path)
    fields = r.get_fields() or {}
    out = []
    for name, fdict in fields.items():
        ft = (fdict.get("/FT") or fdict.get("FT"))
        v  = (fdict.get("/V")  or fdict.get("V"))
        if hasattr(v, "get_object"):
            try:
                v = v.get_object()
            except Exception:
                v = str(v)
        out.append({"pdf_field_name": name, "field_type": str(ft), "value": v})
    return out

# -------------------- Domain knowledge (keywords/labels) --------------------
# You can tailor these lists per template. Defaults here match your uploaded form.

INDIVIDUAL_CLAIM_TYPES = [
    "Accident Benefit","Dread Disease Benefit","Hospitalisation Benefit",
    "Total and Permanent Disability Benefit","Terminal Illness Benefit",
    "Family Waiver Benefit","Major ImpactCritical Impact Benefit",
    "Cancer Hospice Care Benefit","Disability Care Benefit","Senior Illness",
    "Juvenile Illness","Special Illness","Mental Illness","Maternity 360",
    "Lady Plus360 Female Illness","Vital Function Benefit",
    "Cancer TherapyTherapy Support Benefit","Others"
]

INCOMESHIELD_CLAIM_TYPES = [
    "Outpatient treatment","Inpatient Day surgery","Emergency overseas treatment",
    "Daily cash rider","Others_2"
]

AFFINITY_TYPES = ["LUV","SAFRA","CEGIS","HomeTeamNS","OCBC Protect"]

MHS_TYPES = ["Inpatient care"]

EMPLOYMENT = ["Employed","Self Employed","Unemployed"]

PAYMENT_METHODS = {
    "Direct credit": "Direct credit to your bank account",
    "PayNow NRIC/FIN": "PayNow to your NRICFIN linked account",
    "Telegraphic Transfer": "Telegraphic Transfer"
}

CONFINEMENT = ["Bed","House","Hospital"]
CONFINEMENT_CONTROLLER = "c Is the insured currently confined to any of the following Please tick accordingly"
PLEASE_SPECIFY = "Please specify"

# Text fields we want to prioritize as canonical keys (exact labels in this template).
PREFERRED_TEXT_FIELDS = {
    "policy_numbers": "Policy numbers",
    "plan_type": "Plan type",
    "claim_number": "Claim number",
    "insured_full_name": "Full name of insured as shown in NRICFIN cardPassportBirth Certificate",
    "insured_nric": "NRICFINPassportBirth Certificate number of insured",
    "insured_relationship_to_policyholder": "Relationship to policyholder",
    "insured_occupation": "Occupation If unemployed please indicate last occupation",
    "insured_dob_ddmmyyyy": "Date of birth ddmmyyyy",
    "employer_name_address": "Name and address of employer or last employer if unemployed",
    "employment_from_ddmmyyyy": "From",
    "employment_to_ddmmyyyy": "To",
    "duties_at_work": "Duties performed at work",
    "insured_email": "Email address of insured",

    "policyholder_full_name": "Full name as shown in NRICFIN cardPassport of policyholderassignee if policy is assigned",
    "policyholder_nric": "NRICFINPassport number of policyholder assignee if policy is assigned",

    "diagnosis": "i Diagnosis",
    "symptom_start_ddmmyyyy": "ii Date symptoms started ddmmyyyy",
    "symptom_description": "iii Describe in detail all symptoms and nature of medical conditiondisability suffered",

    "accident_date_ddmmyyyy": "i Date of accident ddmmyyyy",
    "accident_time": "ii Time of accident",
    "accident_place": "iii Place of accident",
    "injuries_description": "iv Detailed description of nature of injuriesdisability suffered",
    "accident_description": "v Detailed description of accident Please enclose a copy of the police report if any",
    "accident_dental_details": "vi If you are claiming for accidental injuries resulting in inpatient dental treatment please advise which toothteeth were injured Waswere the injured teeth sound and natural Yes No",

    "confinement_other_specify": "Others_3",
    "confinement_start_ddmmyyyy": "Start Date ddmmyyyy",
    "confinement_end_ddmmyyyy": "End Date ddmmyyyy",
    "daily_activities_desc": "If not confined please briefly describe insureds daily activities",

    "hospital_name_row1": "Name of hospitalRow1",
    "hospital_from_row1_ddmmyyyy": "From ddmmyyyyRow1",
    "hospital_to_row1_ddmmyyyy": "To ddmmyyyyRow1",
    "hospital_name_row2": "Name of hospitalRow2",
    "hospital_from_row2_ddmmyyyy": "From ddmmyyyyRow2",
    "hospital_to_row2_ddmmyyyy": "To ddmmyyyyRow2",
    "hospital_name_row3": "Name of hospitalRow3",
    "hospital_from_row3_ddmmyyyy": "From ddmmyyyyRow3",
    "hospital_to_row3_ddmmyyyy": "To ddmmyyyyRow3",

    "med_leave_start_ddmmyyyy": "Start Date ddmmyyyy_2",
    "med_leave_end_ddmmyyyy": "End Date ddmmyyyy_2",

    "referral_name_addr_1": "Please provide the name and address of referring doctorhospital 1",
    "referral_name_addr_2": "Please provide the name and address of referring doctorhospital 2",

    "doctor_current_name_address": "4 Please provide the name contact number and address of the doctor who is treating the insured for his current conditioninjury",

    "surgery_procedure_row1": "Surgical operationprocedureRow1",
    "surgery_date_row1_ddmmyyyy": "Dates of operationprocedure ddmmyyyyRow1",
    "surgery_code_row1": "Surgical codetable please refer to your doctorRow1",
    "surgery_procedure_row2": "Surgical operationprocedureRow2",
    "surgery_date_row2_ddmmyyyy": "Dates of operationprocedure ddmmyyyyRow2",
    "surgery_code_row2": "Surgical codetable please refer to your doctorRow2",

    "overseas_reason": "a Reason why the insureds conditiondisability is treated outside of Singapore",
    "overseas_left_date_ddmmyyyy": "b Date the insured left Singapore ddmmyyyy",
    "overseas_purpose": "c The purpose of the overseas visit",
    "overseas_visit_from_ddmmyyyy": "From ddmmyyyy",
    "overseas_visit_to_ddmmyyyy": "To ddmmyyyy",

    "prior_name_row1": "Name of doctorRow1",
    "prior_address_row1": "Name and address of clinichospitalRow1",
    "prior_dates_row1_ddmmyyyy": "Dates of consultation ddmmyyyyRow1",
    "prior_reason_row1": "Reasons for consultationRow1",
    "prior_name_row2": "Name of doctorRow2",
    "prior_address_row2": "Name and address of clinichospitalRow2",
    "prior_dates_row2_ddmmyyyy": "Dates of consultation ddmmyyyyRow2",
    "prior_reason_row2": "Reasons for consultationRow2",

    "prior2_name_row1": "Name of doctorRow1_2",
    "prior2_address_row1": "Name and address of clinichospitalRow1_2",
    "prior2_dates_row1_ddmmyyyy": "Dates of consultation ddmmyyyyRow1_2",
    "prior2_reason_row1": "Reasons for consultationRow1_2",
    "prior2_name_row2": "Name of doctorRow2_2",
    "prior2_address_row2": "Name and address of clinichospitalRow2_2",
    "prior2_dates_row2_ddmmyyyy": "Dates of consultation ddmmyyyyRow2_2",
    "prior2_reason_row2": "Reasons for consultationRow2_2",

    "prior3_name_row1": "Name of doctorRow1_3",
    "prior3_address_row1": "Name and address of clinichospitalRow1_3",
    "prior3_dates_row1_ddmmyyyy": "Dates of consultation ddmmyyyyRow1_3",
    "prior3_reason_row1": "Reasons for consultationRow1_3",
    "prior3_name_row2": "Name of doctorRow2_3",
    "prior3_address_row2": "Name and address of clinichospitalRow2_3",
    "prior3_dates_row2_ddmmyyyy": "Dates of consultation ddmmyyyyRow2_3",
    "prior3_reason_row2": "Reasons for consultationRow2_3",

    "other_ins_name_row1": "Name of employer insurance company etcRow1",
    "other_ins_policy_row1": "Policy numberRow1",
    "other_ins_issue_date_row1_ddmmyyyy": "Date of issue ddmmyyyyRow1",
    "other_ins_plan_row1": "Type of planRow1",
    "other_ins_sum_row1": "Claim amount Sum assured SRow1",
    "other_ins_notified_row1": "Claim notified YesNoRow1",
    "other_ins_paid_row1": "Claim paid YesNoRow1",
    "other_ins_name_row2": "Name of employer insurance company etcRow2",
    "other_ins_policy_row2": "Policy numberRow2",
    "other_ins_issue_date_row2_ddmmyyyy": "Date of issue ddmmyyyyRow2",
    "other_ins_plan_row2": "Type of planRow2",
    "other_ins_sum_row2": "Claim amount Sum assured SRow2",
    "other_ins_notified_row2": "Claim notified YesNoRow2",
    "other_ins_paid_row2": "Claim paid YesNoRow2",

    "other_ins_details1": "Details",
    "other_ins_details2": "Details_2",
    "other_ins_details3": "Details_3",
    "other_ins_details4": "Details_4",

    "tt_currency": "Currency for remittance",
    "tt_bank_name": "Name of bank",
    "tt_bank_address": "Bank address",
    "tt_swift": "Swift code",
    "tt_sort_code": "Sort code if applicable",
    "tt_intermediary_name": "Intermediary bank name if applicable",
    "tt_intermediary_country": "Country of intermediary bank if applicable",
    "tt_intermediary_code": "Intermediary bank code Swift code if applicable",
    "tt_remarks": "Remarks any other important information required for transmittance of proceeds",

    "advisor_name": "Name of advisor",
    "advisor_phone": "Contact number of advisor",

    "sig_policyholder_fullname": "Full name as shown in NRICFIN cardPassport and signaturethumbprint of policyholder assignee if policy is assigned",
    "sig_policyholder_nric": "NRICFINPassport number",
    "sig_policyholder_date_ddmmyyyy": "Date signed ddmmyyyy",

    "sig_insured_fullname": "Full name as shown in NRICFIN cardPassport and signaturethumbprint of insured who is 21 years old or above if different from policyholderassignee",
    "sig_insured_nric": "NRICFINPassport number_2",
    "sig_insured_date_ddmmyyyy": "Date signed ddmmyyyy_2",

    "sig_family_fullname": "Full name as shown in NRICFIN cardPassport and signaturethumbprint of family member who is 21 years old or above if claim on family waiver benefit",
    "sig_family_nric": "NRICFINPassport number_3",
    "sig_family_date_ddmmyyyy": "Date signed ddmmyyyy_3",

    "sig_claimant_fullname": "Full name as shown in NRICFIN cardPassport and signature of claimant who is 21 years old or above if the policyholderassigneeinsuredfamily member does not have the mental capacity or is below 21 years old",
    "sig_claimant_nric": "NRICFINPassport number_4",
    "sig_claimant_date_ddmmyyyy": "Date signed ddmmyyyy_4",

    "claimant_relationship_to_policyholder": "Claimants relationship to policyholder",
    "claimant_email": "Email address of claimant",
    "unable_to_sign_reason": "Please indicate why policyholderassigneeinsuredfamily member is unable to sign",
}

# -------------------- Core builder --------------------

def build_mapping(field_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Split into text vs buttons
    texts = [f for f in field_list if (f.get("field_type") or "").endswith("Tx")]
    btns  = [f for f in field_list if (f.get("field_type") or "").endswith("Btn")]

    # 1) Text fields: keep preferred ones, then auto-slug the rest into pdf_fields
    pdf_fields = {}
    # First: add preferred exact labels that are present
    present_labels = {f["pdf_field_name"] for f in texts}
    for canon, label in PREFERRED_TEXT_FIELDS.items():
        if label in present_labels:
            pdf_fields[canon] = label

    # Then add remaining text fields with slug guesses
    used = set(pdf_fields.values())
    for f in texts:
        name = f["pdf_field_name"]
        if name in used: 
            continue
        key = slug(name)
        # avoid collisions with existing keys
        base = key
        i = 2
        while key in pdf_fields:
            key = f"{base}_{i}"
            i += 1
        pdf_fields[key] = name

    # 2) Checkbox groups from known lists
    def pick(names: List[str]) -> Dict[str, str]:
        out = {}
        btn_names = {b["pdf_field_name"] for b in btns}
        for n in names:
            if n in btn_names:
                out[n.replace("_2","").replace("  ", " ")] = n
        return out

    checkboxes_individual = pick(INDIVIDUAL_CLAIM_TYPES)
    checkboxes_incomeshield = pick(INCOMESHIELD_CLAIM_TYPES)
    checkboxes_affinity = pick(AFFINITY_TYPES)
    checkboxes_mhs = pick(MHS_TYPES)

    # Gender: empirically this template uses undefined_3 / undefined_4
    gender_map = {}
    for b in btns:
        if b["pdf_field_name"] in ("undefined_3","undefined_4"):
            # We don't know which is which from dump alone; default to M/F based on typical dump ("undefined_3: On")
            # You can adjust later if needed.
            pass
    # Heuristic: if any of these two has value '/On', call that 'Male' (as seen in your dump)
    val_by_name = {b["pdf_field_name"]: b.get("value") for b in btns}
    if "undefined_3" in val_by_name or "undefined_4" in val_by_name:
        on_name = "undefined_3" if val_by_name.get("undefined_3") in ("/On","/Yes") else "undefined_4"
        off_name = "undefined_4" if on_name=="undefined_3" else "undefined_3"
        gender_map = {"Male": on_name, "Female": off_name}

    # Employment
    employment_map = pick(EMPLOYMENT)

    # Payment method: substring matching
    pm_map = {}
    for label, contains in PAYMENT_METHODS.items():
        for b in btns:
            if contains in b["pdf_field_name"]:
                pm_map[label] = b["pdf_field_name"]

    # Confinement
    confinement_map = {}
    for b in btns:
        if b["pdf_field_name"] == CONFINEMENT_CONTROLLER:
            confinement_map["Confined? (section c) YES/NO"] = b["pdf_field_name"]
    for n in CONFINEMENT:
        for b in btns:
            if b["pdf_field_name"] == n:
                confinement_map[n] = n
    for b in btns:
        if PLEASE_SPECIFY == b["pdf_field_name"]:
            confinement_map["Please specify (enable text field)"] = PLEASE_SPECIFY

    # Advisor preference toggle
    advisor_pref = {}
    for b in btns:
        if b["pdf_field_name"].startswith("I prefer to have the communications relating to this claim copied to the preferred servicing advisor"):
            advisor_pref["Copy communications to preferred advisor"] = b["pdf_field_name"]

    # Misc toggles (Yes/No controllers)
    misc = {}
    ctrl_candidates = [
        "iv Have any of the insureds family members suffered from a similar or related illness",
        "Waswere the injured teeth sound and natural",
        "If Yes please state the start and end date of the hospitalmedical leave",
        "Referral by a General PractitionerSpecialistOther hospital please delete accordingly",
        "A  E department",
        "undefined_17","undefined_18","undefined_19","undefined_20",
        "10 Is the insured covered for medical expenses by any other insurance companyies his employer or any other parties If Yes please state details below",
        "undefined_21","undefined_22","undefined_23"
    ]
    btn_names = {b["pdf_field_name"] for b in btns}
    for c in ctrl_candidates:
        if c in btn_names:
            misc[c] = c

    # Unknown checkboxes/text (to review later)
    known_checkbox_names = set().union(
        checkboxes_individual.values(), checkboxes_incomeshield.values(),
        checkboxes_affinity.values(), checkboxes_mhs.values(),
        employment_map.values(), pm_map.values(),
        confinement_map.values(), advisor_pref.values(), misc.values(),
        set(gender_map.values())
    )
    unknown_checkboxes = [b["pdf_field_name"] for b in btns if b["pdf_field_name"] not in known_checkbox_names]

    unresolved_text_fields = [t["pdf_field_name"] for t in texts if t["pdf_field_name"] not in set(pdf_fields.values())]

    mapping = {
        "template_fingerprint": {
            "title": "Medical/Accident/Living/TPD Claim (Income Insurance)",
            "version_hint": "INCOME/LHO/MALTPD/12/2024",
            "pages": 8
        },
        "pdf_fields": pdf_fields,
        "checkboxes_gender": gender_map,
        "checkboxes_employment_status": employment_map,
        "checkboxes_individual_claim_type": checkboxes_individual,
        "checkboxes_incomeshield_claim_type": checkboxes_incomeshield,
        "checkboxes_affinity_claim_type": checkboxes_affinity,
        "checkboxes_mhs_claim_type": checkboxes_mhs,
        "checkboxes_confinement": confinement_map,
        "checkboxes_payment_method": pm_map,
        "checkboxes_advisor_preference": advisor_pref,
        "checkboxes_misc": misc,
        "checkboxes_unknown": unknown_checkboxes,
        "unresolved_text_fields": unresolved_text_fields
    }
    return mapping

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="Path to PDF (uses pypdf to enumerate fields)")
    ap.add_argument("--dump", help="Path to JSON list of {'pdf_field_name','field_type','value'}")
    ap.add_argument("--out", required=True, help="Where to write the mapping JSON")
    args = ap.parse_args()

    if not args.pdf and not args.dump:
        print("Please provide either --pdf or --dump.", file=sys.stderr)
        sys.exit(2)

    if args.pdf:
        field_list = load_from_pdf(args.pdf)
    else:
        with open(args.dump, "r", encoding="utf-8") as f:
            field_list = json.load(f)

    mapping = build_mapping(field_list)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    print(f"Wrote mapping to {args.out}")

if __name__ == "__main__":
    main()
