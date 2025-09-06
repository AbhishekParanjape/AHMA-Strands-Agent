#!/usr/bin/env python3
"""
Test PDF tools without running the full superagent interactive loop
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only what we need
from strands import Agent, tool

# Define PDF tools directly
@tool
def process_insurance_pdf(pdf_path: str, form_type: str = None, output_path: str = None) -> str:
    """Process an insurance PDF using the existing PDF processing workflow."""
    try:
        import subprocess
        import tempfile
        from pathlib import Path
        
        if not output_path:
            pdf_file = Path(pdf_path)
            output_path = str(pdf_file.parent / f"{pdf_file.stem}_filled{pdf_file.suffix}")
        
        print(f"🔄 Processing PDF: {pdf_path}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            fields_json = os.path.join(temp_dir, "fields.json")
            result = subprocess.run([
                "python", "pdf/json_dump2.py",
                "--pdf", pdf_path,
                "--out", fields_json
            ], check=True, capture_output=True, text=True)
            
            if form_type == "health_declaration":
                example_data = "pdf/health_example_data.json"
            else:
                example_data = "pdf/example_data.json"
            
            values_json = os.path.join(temp_dir, "values.json")
            result = subprocess.run([
                "python", "pdf/fetchdb.py",
                "--dump", fields_json,
                "--example-data", example_data,
                "--out", values_json
            ], check=True, capture_output=True, text=True)
            
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

@tool
def fill_health_declaration_form(pdf_path: str) -> str:
    """Fill out a health declaration form specifically."""
    return process_insurance_pdf(pdf_path, form_type="health_declaration")

@tool
def list_pdf_files(directory: str = "pdf") -> str:
    """List available PDF files in a directory."""
    try:
        from pathlib import Path
        
        pdf_dir = Path(directory)
        if not pdf_dir.exists():
            return f"❌ Directory not found: {directory}"
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            return f"📄 No PDF files found in {directory}"
        
        result = f"📄 Found {len(pdf_files)} PDF file(s) in {directory}:\n\n"
        for i, pdf_file in enumerate(pdf_files, 1):
            result += f"{i}. {pdf_file.name}\n"
            result += f"   Path: {pdf_file}\n"
            result += f"   Size: {pdf_file.stat().st_size} bytes\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing PDF files: {str(e)}"

# Create a simple agent with PDF tools
pdf_agent = Agent(
    name="PDFAgent",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt=(
        "You are a PDF processing agent. You can help with:\n"
        "- Processing insurance PDFs\n"
        "- Filling out health declaration forms\n"
        "- Filling out medical claim forms\n"
        "- Listing available PDF files\n"
        "When a user asks to 'fill up' or 'process' a PDF, use the appropriate tool."
    ),
    tools=[process_insurance_pdf, fill_health_declaration_form, list_pdf_files]
)

def test_pdf_agent():
    """Test the PDF agent with various prompts."""
    print("🧪 Testing PDF agent...")
    
    # Check available tools
    print(f"\n📋 Available tools ({len(pdf_agent.tools)}):")
    for i, tool in enumerate(pdf_agent.tools, 1):
        print(f"  {i}. {tool.__name__}")
    
    # Test prompts
    test_prompts = [
        "Fill up my health-declaration-form.pdf",
        "Process the insurance form at pdf/health-declaration-statement.pdf",
        "List PDF files",
        "Show me available PDF forms"
    ]
    
    print(f"\n🧪 Testing PDF agent responses...")
    for prompt in test_prompts:
        print(f"\nPrompt: '{prompt}'")
        try:
            response = pdf_agent(prompt)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n✅ PDF agent test completed!")

if __name__ == "__main__":
    test_pdf_agent()
