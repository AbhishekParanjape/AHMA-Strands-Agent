from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys
import os
import requests
from dotenv import load_dotenv
import tempfile
import subprocess
import json
from pathlib import Path
from werkzeug.utils import secure_filename

# -----------------------------------------------------------------------------
# Imports & Setup
# -----------------------------------------------------------------------------

# Add the parent directory to the path so we can import superagent_test
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superagent_test import router_agent, analyze_medicine_image
from google_calendar_service import GoogleCalendarService


load_dotenv()  # Load environment variables from .env if present

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Google Calendar service
gcal_service = GoogleCalendarService()

# PDF processing configuration
UPLOAD_FOLDER = 'pdf_uploads'
PROCESSED_FOLDER = 'pdf_processed'
ALLOWED_EXTENSIONS = {'pdf'}

# Medicine images configuration
MED_IMAGES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'med_images_test')
os.makedirs(MED_IMAGES_FOLDER, exist_ok=True)

# Create upload directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _stringify_list(lst):
    try:
        return " ".join(str(x) for x in lst)
    except Exception:
        return str(lst)

def extract_text(result):
    """
    Return a user-facing string from common agent/LLM result shapes.
    Falls back to str(result).
    """
    # Already a string
    if isinstance(result, str):
        return result

    # Handle AgentResult-like objects
    if hasattr(result, 'message') and hasattr(result, 'stop_reason'):
        message = result.message
        if isinstance(message, dict):
            if message.get("role") == "assistant" and "content" in message:
                content = message["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if isinstance(first_item, dict) and "text" in first_item:
                        return first_item["text"]
                    elif isinstance(first_item, str):
                        return first_item
                elif isinstance(content, str):
                    return content
        elif isinstance(message, str):
            return message

    # Dict-like results
    if isinstance(result, dict):
        # Specific shape: {'role': 'assistant', 'content': [{'text': '...'}]}
        if result.get("role") == "assistant" and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    return first_item["text"]
                elif isinstance(first_item, str):
                    return first_item
                else:
                    return _stringify_list(content)
            elif isinstance(content, str):
                return content

        # Common keys
        for key in ("message", "text", "content", "output_text"):
            if key in result:
                val = result[key]
                if isinstance(val, str):
                    return val
                if isinstance(val, list):
                    return _stringify_list(val)
                return str(val)

        # SDKs with lists of messages/choices
        for list_key in ("messages", "outputs", "choices"):
            if list_key in result and isinstance(result[list_key], list):
                for m in reversed(result[list_key]):
                    if isinstance(m, dict):
                        if m.get("role") == "assistant" and "content" in m:
                            content = m["content"]
                            if isinstance(content, list) and len(content) > 0:
                                first_item = content[0]
                                if isinstance(first_item, dict) and "text" in first_item:
                                    return first_item["text"]
                                elif isinstance(first_item, str):
                                    return first_item
                            elif isinstance(content, str):
                                return content
                        if "text" in m and isinstance(m["text"], str):
                            return m["text"]
                return _stringify_list(result[list_key])

        # Fallback: stringify trimmed dict
        return str({k: ("[...]" if len(str(v)) > 200 else v) for k, v in result.items()})

    # Object with common attributes
    for attr in ("output_text", "content", "text", "message"):
        if hasattr(result, attr):
            val = getattr(result, attr)
            if isinstance(val, str):
                return val
            if isinstance(val, list):
                return _stringify_list(val)
            return str(val)

    # Last resort - try any string-like attribute
    if hasattr(result, '__dict__'):
        for key, value in result.__dict__.items():
            if isinstance(value, str) and len(value) > 10:
                return value

    return str(result)

# -----------------------------------------------------------------------------
# Todoist Integration (Real API)
# -----------------------------------------------------------------------------

TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
TODOIST_BASE_URL = "https://api.todoist.com/rest/v2"

def todoist_headers():
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json",
    }

def require_todoist_token():
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "Todoist not configured. Set TODOIST_API_TOKEN in your environment or .env."
        }), 501
    return None

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route('/api/ahma/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that processes user messages through the superagent.
    Returns a top-level 'response' string to avoid [object Object] rendering.
    """
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get('message') or '').strip()

        if not message:
            return jsonify({'error': 'No message provided', 'success': False}), 400

        result = router_agent(message)

        # Debug (optional): uncomment if you want server logs
        # print(f"🔍 Raw superagent result: {repr(result)}")
        # print(f"🔍 Result type: {type(result)}")

        text = extract_text(result)

        return jsonify({'response': text, 'success': True})

    except Exception as e:
        print(f"Error processing chat message: {repr(e)}")
        return jsonify({'error': 'Internal server error', 'success': False}), 500


@app.route('/api/medicine/upload-image', methods=['POST'])
def upload_medicine_image():
    """
    Upload a medicine-related image to med_images_test/ with duplicate detection.
    If not a duplicate, trigger the routing agent to use the Medicine Agent to create events.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Save to a temp buffer to compute hash
        import hashlib
        import io
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Load or create index.json for duplicate tracking
        index_path = os.path.join(MED_IMAGES_FOLDER, 'index.json')
        index = {}
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    index = json.load(f)
            except Exception:
                index = {}

        # Consider duplicate only if at least one existing file with the same hash is still present
        is_duplicate = False
        if file_hash in index:
            existing_files = []
            for fname in index[file_hash].get('filenames', []):
                if os.path.exists(os.path.join(MED_IMAGES_FOLDER, fname)):
                    existing_files.append(fname)
            if existing_files:
                is_duplicate = True
                index[file_hash]['filenames'] = existing_files
            else:
                # All referenced files no longer exist; treat as new upload and reset list
                index[file_hash]['filenames'] = []

        # Use secure filename and ensure unique name
        original_name = secure_filename(file.filename)
        name_no_ext, ext = os.path.splitext(original_name)
        save_name = original_name
        counter = 1
        while os.path.exists(os.path.join(MED_IMAGES_FOLDER, save_name)):
            save_name = f"{name_no_ext}_{counter}{ext}"
            counter += 1

        # Save file
        save_path = os.path.join(MED_IMAGES_FOLDER, save_name)
        with open(save_path, 'wb') as out:
            out.write(file_bytes)

        # Update index
        if file_hash not in index:
            index[file_hash] = {'filenames': [save_name]}
        else:
            if save_name not in index[file_hash]['filenames']:
                index[file_hash]['filenames'].append(save_name)
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        # Build preview URL served by backend
        preview_url = f"/api/medicine/image/{save_name}"

        agent_response = None
        if not is_duplicate:
            try:
                abs_path_for_agent = os.path.abspath(save_path)
                # Directly invoke the analysis tool to avoid routing/text parsing issues
                agent_response = extract_text(analyze_medicine_image(abs_path_for_agent))
            except Exception as e:
                print(f"Error triggering MedicineAgent: {e}")

        return jsonify({
            'success': True,
            'filename': save_name,
            'duplicate': is_duplicate,
            'preview_url': preview_url,
            'agent_response': agent_response
        })

    except Exception as e:
        print(f"Error uploading medicine image: {e}")
        return jsonify({'success': False, 'error': 'Failed to upload image'}), 500


@app.route('/api/medicine/image/<path:filename>', methods=['GET'])
def get_medicine_image(filename):
    """
    Serve an uploaded medicine image from med_images_test/.
    """
    try:
        safe_name = secure_filename(filename)
        image_path = os.path.join(MED_IMAGES_FOLDER, safe_name)
        if not os.path.exists(image_path):
            return jsonify({'success': False, 'error': 'Image not found'}), 404
        return send_file(image_path)
    except Exception as e:
        print(f"Error serving medicine image: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch image'}), 500


@app.route('/api/google-calendar/events', methods=['GET'])
def get_calendar_events():
    """
    Get real Google Calendar events via your GoogleCalendarService,
    with a fallback to mock data if unavailable.
    """
    try:
        max_results = int(request.args.get('max_results', 5))

        events = gcal_service.get_upcoming_events(max_results)

        if events:
            return jsonify({
                'events': events,
                'success': True,
                'source': 'google_calendar'
            })
        else:
            print("⚠️ Google Calendar not available, using mock data")
            mock_events = [
                {
                    'id': 'mock_1',
                    'summary': 'Doctor Appointment',
                    'start': '2024-01-15T10:00:00Z',
                    'end': '2024-01-15T11:00:00Z',
                    'location': 'Changi General Hospital',
                    'description': 'Regular checkup'
                },
                {
                    'id': 'mock_2',
                    'summary': 'Medicine Pickup',
                    'start': '2024-01-16T14:00:00Z',
                    'end': '2024-01-16T14:30:00Z',
                    'location': 'Guardian Pharmacy',
                    'description': 'Prescription refill'
                }
            ]
            return jsonify({
                'events': mock_events[:max_results],
                'success': True,
                'source': 'mock_data'
            })

    except Exception as e:
        print(f"Error fetching calendar events: {str(e)}")
        return jsonify({'error': 'Failed to fetch calendar events', 'success': False}), 500


@app.route('/api/todoist/tasks', methods=['GET'])
def get_todoist_tasks():
    """
    Get real Todoist tasks from the API.
    """
    token_check = require_todoist_token()
    if token_check:
        return token_check

    try:
        limit = int(request.args.get('limit', 10))
        # You can add filters like ?project_id=... or ?filter=...
        resp = requests.get(f"{TODOIST_BASE_URL}/tasks", headers=todoist_headers(), timeout=20)
        resp.raise_for_status()
        tasks = resp.json()
        return jsonify({
            'tasks': tasks[:limit],
            'success': True,
            'source': 'todoist'
        })
    except requests.HTTPError as http_err:
        print(f"Todoist HTTP error: {http_err} | Response: {getattr(http_err, 'response', None) and http_err.response.text}")
        status = http_err.response.status_code if getattr(http_err, 'response', None) else 500
        return jsonify({'error': 'Todoist API error', 'success': False}), status
    except Exception as e:
        print(f"Error fetching Todoist tasks: {e}")
        return jsonify({'error': 'Failed to fetch tasks', 'success': False}), 500


@app.route('/api/todoist/tasks', methods=['POST'])
def add_todoist_task():
    """
    Create a new Todoist task.
    Body: { "content": "Task title", "due_string": "tomorrow 9am", ... }
    """
    token_check = require_todoist_token()
    if token_check:
        return token_check

    try:
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({'error': 'Task content required', 'success': False}), 400

        # Optional passthrough fields (see Todoist docs for more)
        payload = {"content": content}
        for k in ("due_string", "project_id", "priority", "description", "labels", "due_date", "due_datetime"):
            if k in data:
                payload[k] = data[k]

        resp = requests.post(
            f"{TODOIST_BASE_URL}/tasks",
            headers=todoist_headers(),
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        return jsonify({'task': resp.json(), 'success': True})
    except requests.HTTPError as http_err:
        print(f"Todoist HTTP error: {http_err} | Response: {http_err.response.text}")
        status = http_err.response.status_code if getattr(http_err, 'response', None) else 500
        return jsonify({'error': 'Todoist API error', 'success': False}), status
    except Exception as e:
        print(f"Error creating Todoist task: {e}")
        return jsonify({'error': 'Failed to create task', 'success': False}), 500


@app.route('/api/todoist/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """
    Complete (close) a Todoist task.
    """
    token_check = require_todoist_token()
    if token_check:
        return token_check

    try:
        resp = requests.post(
            f"{TODOIST_BASE_URL}/tasks/{task_id}/close",
            headers=todoist_headers(),
            timeout=20
        )
        if resp.status_code == 204:
            return jsonify({'success': True, 'message': f'Task {task_id} completed successfully'})
        else:
            # Todoist sometimes returns JSON error bodies
            try:
                return jsonify({'success': False, 'error': resp.json()}), resp.status_code
            except Exception:
                return jsonify({'success': False, 'error': resp.text}), resp.status_code
    except requests.HTTPError as http_err:
        print(f"Todoist HTTP error: {http_err} | Response: {http_err.response.text}")
        status = http_err.response.status_code if getattr(http_err, 'response', None) else 500
        return jsonify({'error': 'Todoist API error', 'success': False}), status
    except Exception as e:
        print(f"Error completing task: {e}")
        return jsonify({'error': 'Failed to complete task', 'success': False}), 500


# -----------------------------------------------------------------------------
# PDF Processing Routes
# -----------------------------------------------------------------------------

@app.route('/api/pdf/upload', methods=['POST'])
def upload_pdf():
    """
    Upload a PDF file for processing.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'File uploaded successfully'
            })
        else:
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.', 'success': False}), 400
            
    except Exception as e:
        print(f"Error uploading PDF: {str(e)}")
        return jsonify({'error': 'Failed to upload file', 'success': False}), 500

@app.route('/api/pdf/process', methods=['POST'])
def process_pdf():
    """
    Process an uploaded PDF using the PDF processing workflow.
    """
    try:
        data = request.get_json(silent=True) or {}
        filename = data.get('filename', '').strip()
        form_type = data.get('form_type', 'auto')
        
        if not filename:
            return jsonify({'error': 'No filename provided', 'success': False}), 400
        
        # Check if file exists
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        # Generate output filename
        output_filename = f"{Path(filename).stem}_filled{Path(filename).suffix}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        print(f"🔄 Processing PDF: {filename}")
        
        # Step 1: Extract form fields
        with tempfile.TemporaryDirectory() as temp_dir:
            fields_json = os.path.join(temp_dir, "fields.json")
            result = subprocess.run([
                "python", "../pdf/json_dump2.py",
                "--pdf", filepath,
                "--out", fields_json
            ], check=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Step 2: Use appropriate example data based on form type
            if form_type == "health_declaration":
                example_data = "../pdf/health_example_data.json"
            else:
                example_data = "../pdf/example_data.json"
            
            # Step 3: Merge data with fields
            values_json = os.path.join(temp_dir, "values.json")
            result = subprocess.run([
                "python", "../pdf/fetchdb.py",
                "--dump", fields_json,
                "--example-data", example_data,
                "--out", values_json
            ], check=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Step 4: Fill PDF
            result = subprocess.run([
                "python", "../pdf/autofill.py",
                "--pdf-in", filepath,
                "--pdf-out", output_path,
                "--values", values_json
            ], check=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return jsonify({
            'success': True,
            'original_filename': filename,
            'processed_filename': output_filename,
            'form_type': form_type,
            'message': 'PDF processed successfully'
        })
        
    except subprocess.CalledProcessError as e:
        print(f"Error processing PDF: {e.stderr}")
        return jsonify({'error': f'PDF processing failed: {e.stderr}', 'success': False}), 500
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return jsonify({'error': 'Failed to process PDF', 'success': False}), 500

@app.route('/api/pdf/download/<filename>', methods=['GET'])
def download_pdf(filename):
    """
    Download a processed PDF file.
    """
    try:
        filepath = os.path.join(PROCESSED_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"Error downloading PDF: {str(e)}")
        return jsonify({'error': 'Failed to download file', 'success': False}), 500

@app.route('/api/pdf/list', methods=['GET'])
def list_pdfs():
    """
    List uploaded and processed PDF files.
    """
    try:
        uploaded_files = []
        processed_files = []
        
        # List uploaded files
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    stat = os.stat(filepath)
                    uploaded_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'uploaded_at': stat.st_mtime,
                        'type': 'uploaded'
                    })
        
        # List processed files
        if os.path.exists(PROCESSED_FOLDER):
            for filename in os.listdir(PROCESSED_FOLDER):
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(PROCESSED_FOLDER, filename)
                    stat = os.stat(filepath)
                    processed_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'processed_at': stat.st_mtime,
                        'type': 'processed'
                    })
        
        return jsonify({
            'success': True,
            'uploaded_files': uploaded_files,
            'processed_files': processed_files
        })
        
    except Exception as e:
        print(f"Error listing PDFs: {str(e)}")
        return jsonify({'error': 'Failed to list files', 'success': False}), 500

@app.route('/api/pdf/delete/<filename>', methods=['DELETE'])
def delete_pdf(filename):
    """
    Delete a PDF file (uploaded or processed).
    """
    try:
        file_type = request.args.get('type', 'uploaded')  # 'uploaded' or 'processed'
        
        if file_type == 'uploaded':
            filepath = os.path.join(UPLOAD_FOLDER, filename)
        else:
            filepath = os.path.join(PROCESSED_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'File {filename} deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting PDF: {str(e)}")
        return jsonify({'error': 'Failed to delete file', 'success': False}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'message': 'AHMA Backend API is running'
    })


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    print("🚀 Starting AHMA Backend API...")
    print("📡 API will be available at: http://localhost:5001")
    print("🔗 Frontend proxy is configured to connect to this backend")
    app.run(host='0.0.0.0', port=5001, debug=True)

