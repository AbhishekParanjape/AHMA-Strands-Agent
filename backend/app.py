from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import requests
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Imports & Setup
# -----------------------------------------------------------------------------

# Add the parent directory to the path so we can import superagent_test
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superagent_test import router_agent
from google_calendar_service import GoogleCalendarService

load_dotenv()  # Load environment variables from .env if present

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Google Calendar service
gcal_service = GoogleCalendarService()

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

