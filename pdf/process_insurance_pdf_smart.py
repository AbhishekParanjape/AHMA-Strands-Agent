#!/usr/bin/env python3
"""
Smart Insurance PDF Processing Workflow

This script automatically detects the form type and uses appropriate example data:
- Health Declaration forms use health_example_data.json
- Medical/Accident claim forms use example_data.json
- Falls back to manual example data if provided

Usage:
    python process_insurance_pdf_smart.py <input_pdf> [output_pdf] [--example-data <path>] [--keep-intermediate]

Examples:
    python process_insurance_pdf_smart.py "health-declaration-statement.pdf"
    python process_insurance_pdf_smart.py "Medical Accident Living TPD.pdf"
    python process_insurance_pdf_smart.py "any_form.pdf" --example-data "custom_data.json"
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any


def detect_form_type(fields_json: Dict[str, Any]) -> str:
    """
    Detect the form type based on field names.
    Returns: 'health_declaration', 'medical_claim', or 'unknown'
    """
    field_names = list(fields_json.keys())
    field_names_lower = [name.lower() for name in field_names]
    
    # Health declaration indicators
    health_indicators = [
        'policy no', 'nric', 'passport no', 'countryregion code',
        'surrender penalty', 'reinstatement'
    ]
    
    # Medical/Accident claim indicators
    medical_indicators = [
        'accident', 'medical', 'hospital', 'diagnosis', 'symptoms',
        'disability', 'benefit', 'claim number', 'policy numbers'
    ]
    
    health_score = sum(1 for indicator in health_indicators 
                      if any(indicator in field for field in field_names_lower))
    medical_score = sum(1 for indicator in medical_indicators 
                       if any(indicator in field for field in field_names_lower))
    
    if health_score > medical_score and health_score > 0:
        return 'health_declaration'
    elif medical_score > 0:
        return 'medical_claim'
    else:
        return 'unknown'


def get_example_data_path(form_type: str, custom_path: Optional[str] = None) -> str:
    """Get the appropriate example data file path."""
    if custom_path and os.path.exists(custom_path):
        return custom_path
    
    if form_type == 'health_declaration':
        return 'health_example_data.json'
    elif form_type == 'medical_claim':
        return 'example_data.json'
    else:
        # Fallback to default
        return 'example_data.json'


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔄 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Command not found: {e}")
        return False


def process_insurance_pdf_smart(
    input_pdf: str,
    output_pdf: Optional[str] = None,
    example_data: Optional[str] = None,
    keep_intermediate: bool = False
) -> bool:
    """
    Process an insurance PDF with smart form type detection.
    
    Args:
        input_pdf: Path to input PDF file
        output_pdf: Path to output PDF file (optional, defaults to input_pdf with _filled suffix)
        example_data: Path to custom example data JSON file (optional)
        keep_intermediate: Whether to keep intermediate files for debugging
    
    Returns:
        True if successful, False otherwise
    """
    
    # Validate input files
    if not os.path.exists(input_pdf):
        print(f"❌ Input PDF not found: {input_pdf}")
        return False
    
    # Set up file paths
    input_path = Path(input_pdf)
    if output_pdf is None:
        output_pdf = str(input_path.parent / f"{input_path.stem}_filled{input_path.suffix}")
    
    # Create temporary files for intermediate steps
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Step 1: Extract form fields from PDF
        fields_json_path = temp_path / "fields.json"
        if not run_command([
            "python", "json_dump2.py",
            "--pdf", input_pdf,
            "--out", str(fields_json_path)
        ], "Extracting form fields from PDF"):
            return False
        
        # Step 2: Detect form type and select appropriate example data
        try:
            with open(fields_json_path, "r", encoding="utf-8") as f:
                fields_data = json.load(f)
            
            form_type = detect_form_type(fields_data)
            example_data_path = get_example_data_path(form_type, example_data)
            
            print(f"\n🔍 Detected form type: {form_type}")
            print(f"📄 Using example data: {example_data_path}")
            
            if not os.path.exists(example_data_path):
                print(f"❌ Example data file not found: {example_data_path}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to detect form type: {e}")
            return False
        
        # Step 3: Merge with example data
        values_json = temp_path / "values.json"
        if not run_command([
            "python", "fetchdb.py",
            "--dump", str(fields_json_path),
            "--example-data", example_data_path,
            "--out", str(values_json)
        ], "Merging with example data"):
            return False
        
        # Step 4: Fill the PDF
        if not run_command([
            "python", "autofill.py",
            "--pdf-in", input_pdf,
            "--pdf-out", output_pdf,
            "--values", str(values_json)
        ], "Filling PDF with merged data"):
            return False
        
        # Copy intermediate files if requested
        if keep_intermediate:
            intermediate_dir = Path("intermediate_files")
            intermediate_dir.mkdir(exist_ok=True)
            
            import shutil
            shutil.copy2(fields_json_path, intermediate_dir / f"{input_path.stem}_fields.json")
            shutil.copy2(values_json, intermediate_dir / f"{input_path.stem}_values.json")
            
            print(f"📁 Intermediate files saved to: {intermediate_dir}")
    
    print(f"\n🎉 Success! Filled PDF saved to: {output_pdf}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Process insurance PDFs with smart form type detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "input_pdf",
        help="Path to input PDF file"
    )
    
    parser.add_argument(
        "output_pdf",
        nargs="?",
        help="Path to output PDF file (optional, defaults to input_pdf with _filled suffix)"
    )
    
    parser.add_argument(
        "--example-data",
        help="Path to custom example data JSON file (optional, auto-detected if not provided)"
    )
    
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep intermediate JSON files for debugging"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Change to the script directory to ensure relative paths work
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🏥 Smart Insurance PDF Processing Workflow")
    print("=" * 50)
    print(f"Input PDF: {args.input_pdf}")
    print(f"Output PDF: {args.output_pdf or 'auto-generated'}")
    print(f"Custom Example Data: {args.example_data or 'auto-detected'}")
    print(f"Keep Intermediate: {args.keep_intermediate}")
    
    success = process_insurance_pdf_smart(
        input_pdf=args.input_pdf,
        output_pdf=args.output_pdf,
        example_data=args.example_data,
        keep_intermediate=args.keep_intermediate
    )
    
    if success:
        print("\n✅ Workflow completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Workflow failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
