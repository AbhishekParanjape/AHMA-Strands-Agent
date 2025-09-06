#!/usr/bin/env python3
"""
Direct test of PDF tools without running the full superagent
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the tools directly
from strands import tool

@tool
def process_insurance_pdf(pdf_path: str, form_type: str = None, output_path: str = None) -> str:
    """
    Process an insurance PDF using the existing PDF processing workflow.
    """
    try:
        import subprocess
        import tempfile
        from pathlib import Path
        
        # Generate output path if not provided
        if not output_path:
            pdf_file = Path(pdf_path)
            output_path = str(pdf_file.parent / f"{pdf_file.stem}_filled{pdf_file.suffix}")
        
        print(f"🔄 Processing PDF: {pdf_path}")
        
        # Step 1: Extract form fields
        with tempfile.TemporaryDirectory() as temp_dir:
            fields_json = os.path.join(temp_dir, "fields.json")
            result = subprocess.run([
                "python", "pdf/json_dump2.py",
                "--pdf", pdf_path,
                "--out", fields_json
            ], check=True, capture_output=True, text=True)
            
            # Step 2: Use appropriate example data based on form type
            if form_type == "health_declaration":
                example_data = "pdf/health_example_data.json"
            else:
                example_data = "pdf/example_data.json"
            
            # Step 3: Merge data with fields
            values_json = os.path.join(temp_dir, "values.json")
            result = subprocess.run([
                "python", "pdf/fetchdb.py",
                "--dump", fields_json,
                "--example-data", example_data,
                "--out", values_json
            ], check=True, capture_output=True, text=True)
            
            # Step 4: Fill PDF
            result = subprocess.run([
                "python", "pdf/autofill.py",
                "--pdf-in", pdf_path,
                "--pdf-out", output_path,
                "--values", values_json
            ], check=True, capture_output=True, text=True)
        
        return f"✅ PDF processed successfully!\n\n" \
               f"📄 Input PDF: {pdf_path}\n" \
               f"📄 Output PDF: {output_path}\n" \
               f"🏷️ Form type: {form_type or 'auto-detected'}\n" \
               f"📊 Processing completed successfully!"
               
    except subprocess.CalledProcessError as e:
        return f"❌ Error processing PDF: {e.stderr}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

def test_pdf_processing():
    """Test PDF processing directly."""
    print("🧪 Testing PDF processing directly...")
    
    # Test with existing PDF
    test_pdf = "pdf/health-declaration-statement.pdf"
    if os.path.exists(test_pdf):
        print(f"Testing with: {test_pdf}")
        result = process_insurance_pdf(test_pdf, form_type="health_declaration")
        print(result)
        return True
    else:
        print(f"Test PDF not found: {test_pdf}")
        return False

if __name__ == "__main__":
    test_pdf_processing()
