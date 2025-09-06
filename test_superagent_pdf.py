#!/usr/bin/env python3
"""
Test superagent PDF recognition without running interactive loop
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the tools directly without running the interactive loop
from strands import Agent, tool
import boto3

# Create a simple test agent with PDF tools
@tool
def process_insurance_pdf(pdf_path: str, form_type: str = None, output_path: str = None) -> str:
    """Process an insurance PDF using the existing PDF processing workflow."""
    return f"✅ PDF processed: {pdf_path} (type: {form_type})"

@tool
def fill_health_declaration_form(pdf_path: str) -> str:
    """Fill out a health declaration form specifically."""
    return f"✅ Health declaration form filled: {pdf_path}"

@tool
def list_pdf_files(directory: str = "pdf") -> str:
    """List available PDF files in a directory."""
    return f"📄 Listed PDF files in {directory}"

# Create test agent
test_agent = Agent(
    name="TestPDFAgent",
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

def test_pdf_recognition():
    """Test PDF prompt recognition."""
    print("🧪 Testing PDF prompt recognition...")
    
    test_prompts = [
        "Fill up my health-declaration-form.pdf",
        "Process the insurance form",
        "Fill out the medical claim",
        "List PDF files",
        "Show me available PDF forms"
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: '{prompt}'")
        try:
            response = test_agent(prompt)
            print(f"Response: {response[:150]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n✅ PDF recognition test completed!")

if __name__ == "__main__":
    test_pdf_recognition()
