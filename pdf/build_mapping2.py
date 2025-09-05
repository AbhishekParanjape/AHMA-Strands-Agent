import PyPDF2
import re
from typing import Dict, List, Optional
import argparse, json, sys


def extract_field_names_comprehensive(pdf_path: str) -> Dict[str, Dict]:
    """
    Extract AcroForm field names using multiple methods to get the most accurate names.
    """
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        if "/AcroForm" not in pdf_reader.trailer["/Root"]:
            print("No AcroForm found in PDF")
            return {}
        
        all_fields = {}
        
        # Method 1: Get text fields directly (most reliable)
        text_fields = extract_text_field_names(pdf_reader)
        all_fields.update(text_fields)
        
        # Method 2: Parse AcroForm structure directly
        acroform_fields = extract_acroform_field_names(pdf_reader)
        all_fields.update(acroform_fields)
        
        # Method 3: Extract from annotations on each page
        annotation_fields = extract_annotation_field_names(pdf_reader)
        all_fields.update(annotation_fields)
        
        # Clean and enhance field names

        enhanced_fields = enhance_field_names(all_fields)
        # After merging all methods:

        
        return enhanced_fields

def extract_text_field_names(pdf_reader: PyPDF2.PdfReader) -> Dict[str, Dict]:
    """Method 1: Extract text field names directly."""
    fields = {}
    
    try:
        # This is the most reliable method for text fields
        text_fields = pdf_reader.get_form_text_fields() or {}
        
        for field_name, field_value in text_fields.items():
            fields[field_name] = {
                'raw_name': field_name,
                'type': 'text',
                'value': field_value,
                'extraction_method': 'get_form_text_fields',
                'page': None
            }
            
    except Exception as e:
        print(f"Error extracting text fields: {e}")
    
    return fields

def extract_acroform_field_names(pdf_reader: PyPDF2.PdfReader) -> Dict[str, Dict]:
    """Method 2: Extract field names from AcroForm structure."""
    fields = {}
    
    try:
        acroform = pdf_reader.trailer["/Root"]["/AcroForm"]
        
        if "/Fields" in acroform:
            for field_ref in acroform["/Fields"]:
                field_obj = field_ref.get_object()
                field_info = parse_field_object(field_obj, pdf_reader)
                
                if field_info and field_info['name']:
                    fields[field_info['name']] = field_info
                    
    except Exception as e:
        print(f"Error extracting AcroForm fields: {e}")
    
    return fields

def parse_field_object(field_obj, pdf_reader: PyPDF2.PdfReader, parent_name: str = "") -> Optional[Dict]:
    """Parse individual field object to extract comprehensive information."""
    try:
        field_info = {
            'raw_name': None,
            'name': None,
            'type': 'unknown',
            'value': None,
            'rect': None,
            'page': None,
            'extraction_method': 'acroform_parse',
            'flags': None,
            'options': None,
            'default_value': None
        }
        
        # Get field name - this is the key part!
        field_name = None
        
        # Check for partial name (/T)
        if "/T" in field_obj:
            partial_name = str(field_obj["/T"])
            field_name = f"{parent_name}.{partial_name}" if parent_name else partial_name
        
        # If no name but has parent, it might be inherited
        elif parent_name:
            field_name = parent_name
            
        if not field_name:
            return None
            
        field_info['raw_name'] = field_name
        field_info['name'] = field_name
        
        # Get field type
        if "/FT" in field_obj:
            field_type_obj = field_obj["/FT"]
            field_type = str(field_type_obj)
            field_info['type'] = {
                "/Tx": "text",
                "/Ch": "choice",
                "/Btn": "button",
                "/Sig": "signature"
            }.get(field_type, field_type)
        
        # Get current value
        if "/V" in field_obj:
            field_info['value'] = str(field_obj["/V"])
        
        # Get default value
        if "/DV" in field_obj:
            field_info['default_value'] = str(field_obj["/DV"])
        
        # Get field rectangle (position)
        if "/Rect" in field_obj:
            field_info['rect'] = [float(x) for x in field_obj["/Rect"]]
        
        # Get field flags
        if "/Ff" in field_obj:
            field_info['flags'] = int(field_obj["/Ff"])
        
        # For choice fields, get options
        if field_info['type'] == "choice" and "/Opt" in field_obj:
            options = []
            for opt in field_obj["/Opt"]:
                if isinstance(opt, list):
                    options.append([str(x) for x in opt])
                else:
                    options.append(str(opt))
            field_info['options'] = options
        
        # Find page number
        field_info['page'] = find_field_page_number(field_obj, pdf_reader)
        
        # Handle child fields (for hierarchical field names)
        child_fields = {}
        if "/Kids" in field_obj:
            for kid_ref in field_obj["/Kids"]:
                kid_obj = kid_ref.get_object()
                kid_info = parse_field_object(kid_obj, pdf_reader, field_name)
                if kid_info and kid_info['name']:
                    child_fields[kid_info['name']] = kid_info
        
        return field_info, child_fields if child_fields else field_info
        
    except Exception as e:
        print(f"Error parsing field object: {e}")
        return None

def extract_annotation_field_names(pdf_reader: PyPDF2.PdfReader) -> Dict[str, Dict]:
    """Method 3: Extract field names from page annotations."""
    fields = {}
    
    for page_num, page in enumerate(pdf_reader.pages):
        try:
            if "/Annots" in page:
                for annot_ref in page["/Annots"]:
                    annot_obj = annot_ref.get_object()
                    
                    # Check if annotation is a widget (form field)
                    if "/Subtype" in annot_obj and str(annot_obj["/Subtype"]) == "/Widget":
                        field_info = extract_widget_field_info(annot_obj, page_num)
                        
                        if field_info and field_info['name']:
                            fields[field_info['name']] = field_info
                            
        except Exception as e:
            print(f"Error extracting annotations from page {page_num}: {e}")
    
    return fields

def extract_widget_field_info(widget_obj, page_num: int) -> Optional[Dict]:
    """Extract field information from widget annotation."""
    try:
        field_info = {
            'raw_name': None,
            'name': None,
            'type': 'widget',
            'value': None,
            'rect': None,
            'page': page_num,
            'extraction_method': 'annotation_widget'
        }
        
        # Get field name from widget
        if "/T" in widget_obj:
            field_name = str(widget_obj["/T"])
            field_info['raw_name'] = field_name
            field_info['name'] = field_name
        
        # Get parent field name if this is a child widget
        elif "/Parent" in widget_obj:
            parent_obj = widget_obj["/Parent"].get_object()
            if "/T" in parent_obj:
                field_name = str(parent_obj["/T"])
                field_info['raw_name'] = field_name
                field_info['name'] = field_name
        
        # Get rectangle
        if "/Rect" in widget_obj:
            field_info['rect'] = [float(x) for x in widget_obj["/Rect"]]
        
        # Get value
        if "/V" in widget_obj:
            field_info['value'] = str(widget_obj["/V"])
        
        return field_info if field_info['name'] else None
        
    except Exception as e:
        print(f"Error extracting widget info: {e}")
        return None

def find_field_page_number(field_obj, pdf_reader: PyPDF2.PdfReader) -> Optional[int]:
    """Find which page a field belongs to."""
    try:
        # Method 1: Direct page reference
        if "/P" in field_obj:
            page_ref = field_obj["/P"]
            for page_num, page in enumerate(pdf_reader.pages):
                if page.indirect_reference == page_ref:
                    return page_num
        
        # Method 2: Check annotations on each page
        for page_num, page in enumerate(pdf_reader.pages):
            if "/Annots" in page:
                for annot_ref in page["/Annots"]:
                    if annot_ref.get_object() == field_obj:
                        return page_num
        
        return None
        
    except Exception:
        return None
    


def enhance_field_names(fields: Dict[str, Dict]) -> Dict[str, Dict]:
    """Clean and enhance field names for better usability."""
    enhanced_fields = {}
    
    for field_name, field_info in fields.items():
        enhanced_info = field_info.copy()
        
        # Create cleaned/human-readable name
        enhanced_info['clean_name'] = clean_field_name(field_name)
        enhanced_info['human_readable_name'] = make_human_readable(field_name)
        
        # Detect field purpose from name
        enhanced_info['detected_purpose'] = detect_field_purpose(field_name)
        
        enhanced_fields[field_name] = enhanced_info
    
    return enhanced_fields

# Clean out generic/noisy field names like "Check Box##" or "Undefined_##"
def _filter_noise_fields(fields: Dict[str, Dict]) -> Dict[str, Dict]:
    out = {}
    for k, v in fields.items():
        raw = v.get('raw_name') or k
        if not _is_noise_field(raw) and not _is_noise_field(k):
            out[k] = v
    return out



def clean_field_name(field_name: str) -> str:
    """Clean field name by removing common prefixes/suffixes and artifacts."""
    # Remove common prefixes
    prefixes_to_remove = ['form.', 'field.', 'input.', 'txt', 'text']
    clean_name = field_name.lower()
    
    for prefix in prefixes_to_remove:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
    
    # Remove common suffixes
    suffixes_to_remove = ['.text', '.value', '.input', '_text', '_field']
    for suffix in suffixes_to_remove:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)]
    
    return clean_name.strip('._- ')

def make_human_readable(field_name: str) -> str:
    """Convert field name to human-readable format."""
    # Start with clean name
    readable = clean_field_name(field_name)
    
    # Replace separators with spaces
    readable = re.sub(r'[._-]+', ' ', readable)
    
    # Handle camelCase
    readable = re.sub(r'([a-z])([A-Z])', r'\1 \2', readable)
    
    # Capitalize words
    readable = ' '.join(word.capitalize() for word in readable.split())
    
    return readable

def detect_field_purpose(field_name: str) -> str:
    """Detect the likely purpose of a field based on its name."""
    name_lower = field_name.lower()
    
    # Define purpose patterns
    purposes = {
        'name': ['name', 'fullname', 'firstname', 'lastname', 'fname', 'lname'],
        'email': ['email', 'mail', 'e_mail'],
        'phone': ['phone', 'tel', 'telephone', 'mobile', 'cell'],
        'address': ['address', 'street', 'city', 'state', 'zip', 'postal'],
        'date': ['date', 'birthday', 'birth', 'dob', 'created', 'modified'],
        'amount': ['amount', 'price', 'cost', 'total', 'sum', 'value'],
        'signature': ['signature', 'sign', 'signed'],
        'checkbox': ['check', 'agree', 'accept', 'confirm'],
        'id': ['id', 'number', 'ssn', 'license', 'account']
    }
    
    for purpose, keywords in purposes.items():
        if any(keyword in name_lower for keyword in keywords):
            return purpose
    
    return 'general'

def print_field_names_analysis(fields: Dict[str, Dict]):
    """Print detailed analysis of field names."""
    print("\n=== FIELD NAMES ANALYSIS ===")
    print(f"Total fields found: {len(fields)}")
    
    # Group by extraction method
    by_method = {}
    for field_name, field_info in fields.items():
        method = field_info.get('extraction_method', 'unknown')
        if method not in by_method:
            by_method[method] = []
        by_method[method].append(field_name)
    
    print(f"\nFields by extraction method:")
    for method, field_list in by_method.items():
        print(f"  {method}: {len(field_list)} fields")
    
    print(f"\nDetailed field information:")
    for field_name, field_info in fields.items():
        print(f"\n--- {field_name} ---")
        print(f"  Raw name: {field_info['raw_name']}")
        print(f"  Clean name: {field_info.get('clean_name', 'N/A')}")
        print(f"  Human readable: {field_info.get('human_readable_name', 'N/A')}")
        print(f"  Type: {field_info['type']}")
        print(f"  Purpose: {field_info.get('detected_purpose', 'N/A')}")
        print(f"  Page: {field_info.get('page', 'Unknown')}")
        print(f"  Current value: {field_info.get('value', 'None')}")
        print(f"  Method: {field_info.get('extraction_method', 'Unknown')}")

# Example usage


# Example usage
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="Path to PDF (uses pypdf to enumerate fields)")
    args = ap.parse_args()
    
    args.out = f"{args.pdf}.json"
    # Example usage
      # Replace with your PDF path
    
    try:
        fields_with_labels = extract_field_names_comprehensive(args.pdf)
        print_field_names_analysis(fields_with_labels)

        
        
        # Convert to JSON for your pipeline
        
        """print("\n=== JSON OUTPUT ===")
        print(json.dumps(fields_with_labels, indent=2, default=str))"""
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(fields_with_labels, f, indent=2, ensure_ascii=False)
            print(f"Wrote mapping to {args.out}")
        
    except FileNotFoundError:
        print(f"PDF file not found: {args.pdf}")
    except Exception as e:
        print(f"Error processing PDF: {e}")