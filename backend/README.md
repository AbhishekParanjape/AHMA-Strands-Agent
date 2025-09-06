# AHMA Backend API

A simple Flask backend API that integrates with the AHMA superagent for the frontend chatbot.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the required environment variables or AWS credentials configured for the superagent.

3. Run the backend:
```bash
python app.py
```

The API will be available at `http://localhost:5001`

## API Endpoints

- `POST /api/ahma/chat` - Main chat endpoint that processes messages through the superagent
- `GET /api/google-calendar/events` - Mock calendar events (can be replaced with real Google Calendar API)
- `GET /api/todoist/tasks` - Mock Todoist tasks (can be replaced with real Todoist API)
- `POST /api/todoist/tasks/<task_id>/complete` - Mock task completion
- `GET /health` - Health check endpoint

## Frontend Integration

The frontend is configured to proxy requests to this backend via the `proxy` setting in `package.json`.

## Development

The backend runs in debug mode by default. Make sure to have all the required dependencies from the main project installed as well, since the superagent imports various modules from the parent directory.

