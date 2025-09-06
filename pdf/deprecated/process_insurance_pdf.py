#!/usr/bin/env python3
"""
Insurance PDF Processing Workflow

This script automates the complete workflow for processing insurance PDFs:
1. Extract form fields from PDF using json_dump2.py
2. Merge with example data using fetchdb.py
3. Fill the PDF with the merged data using autofill.py

Usage:
    python process_insurance_pdf.py <input_pdf> [output_pdf] [--example-data <path>] [--keep-intermediate]

Examples:
    python process_insurance_pdf.py "Medical Accident Living TPD.pdf"
    python process_insurance_pdf.py "Medical Accident Living TPD.pdf" "filled_output.pdf"
    python process_insurance_pdf.py "Medical Accident Living TPD.pdf" --example-data "custom_data.json"
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


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


def process_insurance_pdf(
    input_pdf: str,
    output_pdf: Optional[str] = None,
    example_data: str = "example_data.json",
    keep_intermediate: bool = False
) -> bool:
    """
    Process an insurance PDF through the complete workflow.
    
    Args:
        input_pdf: Path to input PDF file
        output_pdf: Path to output PDF file (optional, defaults to input_pdf with _filled suffix)
        example_data: Path to example data JSON file
        keep_intermediate: Whether to keep intermediate files for debugging
    
    Returns:
        True if successful, False otherwise
    """
    
    # Validate input files
    if not os.path.exists(input_pdf):
        print(f"❌ Input PDF not found: {input_pdf}")
        return False
    
    if not os.path.exists(example_data):
        print(f"❌ Example data file not found: {example_data}")
        return False
    
    # Set up file paths
    input_path = Path(input_pdf)
    if output_pdf is None:
        output_pdf = str(input_path.parent / f"{input_path.stem}_filled{input_path.suffix}")
    
    # Create temporary files for intermediate steps
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Step 1: Extract form fields from PDF
        fields_json = temp_path / "fields.json"
        if not run_command([
            "python", "json_dump2.py",
            "--pdf", input_pdf,
            "--out", str(fields_json)
        ], "Extracting form fields from PDF"):
            return False
        
        # Step 2: Merge with example data
        values_json = temp_path / "values.json"
        if not run_command([
            "python", "fetchdb.py",
            "--dump", str(fields_json),
            "--example-data", example_data,
            "--out", str(values_json)
        ], "Merging with example data"):
            return False
        
        # Step 3: Fill the PDF
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
            shutil.copy2(fields_json, intermediate_dir / f"{input_path.stem}_fields.json")
            shutil.copy2(values_json, intermediate_dir / f"{input_path.stem}_values.json")
            
            print(f"📁 Intermediate files saved to: {intermediate_dir}")
    
    print(f"\n🎉 Success! Filled PDF saved to: {output_pdf}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Process insurance PDFs through the complete workflow",
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
        default="example_data.json",
        help="Path to example data JSON file (default: example_data.json)"
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
    
    print("🏥 Insurance PDF Processing Workflow")
    print("=" * 50)
    print(f"Input PDF: {args.input_pdf}")
    print(f"Output PDF: {args.output_pdf or 'auto-generated'}")
    print(f"Example Data: {args.example_data}")
    print(f"Keep Intermediate: {args.keep_intermediate}")
    
    success = process_insurance_pdf(
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
