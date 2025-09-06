from strands import Agent, tool
import boto3
import os

from reminders_agent.medicine_agent import create_medicine_agent
from reminders_agent.appointments_agent import create_appointments_agent
from tracking_agent.todo_agent import create_todo_agent
from reminders_agent.wellbeing_agent import create_wellbeing_agent

# PDF processing tools will be defined below

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
    aws_secret_access_key="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"
)

# Create sub-agents
@tool
def medicine_agent(query: str) -> str:
    """
    This tool handles queries related to medicine reminders. 
    It forwards the query to the Medicine Agent and returns the response.
    Example: 'Remind me to take Amoxicillin at 9 AM tomorrow.'
    """
    agent = create_medicine_agent()
    return agent(query)

@tool
def appointment_agent(query: str) -> str:
    """
    This tool handles queries related to appointments. 
    It forwards the query to the Appointments Agent and returns the response, including a link to the google calendar event.
    Example: 'Schedule a meeting with John tomorrow at 3 PM.'
    """
    agent = create_appointments_agent()
    return agent(query)

@tool
def todo_agent(query: str) -> str:
    """
    This tool handles queries related to general to-do tasks.
    It forwards the query to the Todo Agent and returns the response.
    Example: 'Add water plants to my to-do list for tomorrow.'
    """
    agent = create_todo_agent()
    return agent(query)


@tool
def wellbeing_agent(query: str) -> str:
    """
    Handle caregiver wellbeing requests. 
    Can provide self-care advice, suggest resources, and schedule wellbeing activities. 
    """
    agent = create_wellbeing_agent()
    return agent(query)

# PDF Processing Tools
@tool
def process_insurance_pdf(pdf_path: str, form_type: str = None, output_path: str = None) -> str:
    """
    Process an insurance PDF using the existing PDF processing workflow.
    
    This tool extracts form fields from a PDF, generates appropriate data, and fills the PDF.
    It can handle health declaration forms, medical claim forms, and other insurance documents.
    
    Args:
        pdf_path: Path to the PDF file (local path or filename)
        form_type: Type of form for better data generation (optional)
                  - "health_declaration" for health declaration forms
                  - "medical_claim" for medical/accident claim forms
        output_path: Path for the filled PDF output (optional, auto-generated if not provided)
    
    Returns:
        String with processing results and file locations
    
    Examples:
        - "Process the PDF at /path/to/insurance_form.pdf"
        - "Fill up my health-declaration-form.pdf"
        - "Process the medical claim PDF with form type medical_claim"
    """
    try:
        import subprocess
        import json
        import tempfile
        from pathlib import Path
        
        # Try to find the PDF file in common locations
        actual_pdf_path = None
        search_paths = [
            pdf_path,  # Try the path as provided
            f"pdf/{pdf_path}",  # Try in pdf directory
            f"backend/pdf_uploads/{pdf_path}",  # Try in backend uploads
            f"pdf/{pdf_path}.pdf" if not pdf_path.endswith('.pdf') else f"pdf/{pdf_path}",  # Try with .pdf extension
        ]
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                actual_pdf_path = search_path
                break
        
        if not actual_pdf_path:
            # List available PDFs to help user
            available_pdfs = []
            for search_dir in ["pdf", "backend/pdf_uploads"]:
                if os.path.exists(search_dir):
                    for file in os.listdir(search_dir):
                        if file.lower().endswith('.pdf'):
                            available_pdfs.append(f"{search_dir}/{file}")
            
            if available_pdfs:
                return f"❌ PDF file '{pdf_path}' not found.\n\n" \
                       f"📁 Available PDF files:\n" + \
                       "\n".join([f"  • {pdf}" for pdf in available_pdfs]) + \
                       f"\n\n💡 Please use one of the available files above, or upload a new PDF through the frontend."
            else:
                return f"❌ PDF file '{pdf_path}' not found and no PDF files are available.\n\n" \
                       f"💡 Please upload a PDF file through the frontend first, or provide the full path to your PDF file."
        
        # Generate output path if not provided
        if not output_path:
            pdf_file = Path(actual_pdf_path)
            output_path = str(pdf_file.parent / f"{pdf_file.stem}_filled{pdf_file.suffix}")
        
        print(f"🔄 Processing PDF: {actual_pdf_path}")
        
        # Step 1: Extract form fields
        with tempfile.TemporaryDirectory() as temp_dir:
            fields_json = os.path.join(temp_dir, "fields.json")
            result = subprocess.run([
                "python", "pdf/json_dump2.py",
                "--pdf", actual_pdf_path,
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
                "--pdf-in", actual_pdf_path,
                "--pdf-out", output_path,
                "--values", values_json
            ], check=True, capture_output=True, text=True)
        
        return f"✅ PDF processed successfully!\n\n" \
               f"📄 Input PDF: {actual_pdf_path}\n" \
               f"📄 Output PDF: {output_path}\n" \
               f"🏷️ Form type: {form_type or 'auto-detected'}\n" \
               f"📊 Processing completed successfully!"
               
    except subprocess.CalledProcessError as e:
        return f"❌ Error processing PDF: {e.stderr}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

@tool
def fill_health_declaration_form(pdf_path: str) -> str:
    """
    Fill out a health declaration form specifically.
    
    This tool is optimized for health declaration forms and will use appropriate
    sample data for fields like policy number, NRIC, contact details, etc.
    
    Args:
        pdf_path: Path to the health declaration PDF file (can be just filename)
    
    Returns:
        String with processing results
    
    Examples:
        - "Fill up my health-declaration-form.pdf"
        - "Process the health declaration at /path/to/health_form.pdf"
    """
    return process_insurance_pdf(pdf_path, form_type="health_declaration")

@tool
def fill_medical_claim_form(pdf_path: str) -> str:
    """
    Fill out a medical claim form specifically.
    
    This tool is optimized for medical and accident claim forms and will use
    appropriate sample data for fields like diagnosis, hospital details, etc.
    
    Args:
        pdf_path: Path to the medical claim PDF file (can be just filename)
    
    Returns:
        String with processing results
    
    Examples:
        - "Fill up my medical-claim-form.pdf"
        - "Process the accident claim at /path/to/claim_form.pdf"
    """
    return process_insurance_pdf(pdf_path, form_type="medical_claim")

@tool
def list_pdf_files(directory: str = "all") -> str:
    """
    List available PDF files in common directories.
    
    Args:
        directory: Directory to search for PDF files (default: "all" searches common locations)
    
    Returns:
        String with list of PDF files
    
    Examples:
        - "List PDF files"
        - "Show me available PDF forms"
    """
    try:
        from pathlib import Path
        
        # Define common PDF directories to search
        search_dirs = []
        if directory == "all":
            search_dirs = ["pdf", "backend/pdf_uploads", "backend/pdf_processed"]
        else:
            search_dirs = [directory]
        
        all_pdf_files = []
        
        for search_dir in search_dirs:
            pdf_dir = Path(search_dir)
            if pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))
                for pdf_file in pdf_files:
                    all_pdf_files.append({
                        'name': pdf_file.name,
                        'path': str(pdf_file),
                        'size': pdf_file.stat().st_size,
                        'directory': search_dir
                    })
        
        if not all_pdf_files:
            return f"📄 No PDF files found in any of the common directories.\n\n" \
                   f"💡 Try uploading a PDF through the frontend first, or place PDF files in the 'pdf' directory."
        
        result = f"📄 Found {len(all_pdf_files)} PDF file(s):\n\n"
        for i, pdf_info in enumerate(all_pdf_files, 1):
            result += f"{i}. {pdf_info['name']}\n"
            result += f"   📁 Directory: {pdf_info['directory']}\n"
            result += f"   📍 Path: {pdf_info['path']}\n"
            result += f"   📊 Size: {pdf_info['size']} bytes\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing PDF files: {str(e)}"

# Router agent
router_agent = Agent(
    name="RouterAgent",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt=(
        "You are a routing agent. Decide whether a user request is about:\n"
        "- Medicine specific details, like name and frequency (send to MedicineAgent)\n"
        "- Calendar Appointments (send to AppointmentAgent)\n"
        "- General to-do tasks, usually including verbs (send to TodoistAgent)\n"
        "- Caregiver wellbeing (self-care, stress, resources) (send to WellbeingAgent)\n"
        "- PDF processing, insurance forms, document filling (use PDF tools)\n"
        "  * Keywords: 'fill up', 'process PDF', 'health declaration', 'medical claim', 'insurance form', 'PDF form'\n"
        "  * Examples: 'Fill up my health-declaration-form.pdf', 'Process the insurance form', 'Fill out the medical claim'\n"
        "- If unsure, confirm with the user on which function they would like to use.\n"
        "Forward the request to the correct agent and return their response."
    ),
    tools=[medicine_agent, appointment_agent, todo_agent, wellbeing_agent, 
           process_insurance_pdf, fill_health_declaration_form, fill_medical_claim_form, list_pdf_files]
)

# ---------- Example usage ----------
'''user_message1 = "Please remind me to take Amoxicillin three times a day for 7 days."
response1 = router_agent(user_message1)
print("user 1:", response1)

user_message2 = "Book a lunch with Sarah tomorrow at 12 at Marina Bay Sands."
response2 = router_agent(user_message2)
print("user 2:", response2)'''

"""user_message3 = "Add a todo: water the plants tomorrow morning."
response3 = router_agent(user_message3)
print("user 3:", response3)
"""

# user_message3 = "Collect the medicine from the doctors at 9am 30 sept 2025, in singapore."

if __name__ == "__main__":
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break

        response3 = router_agent(user_input)
