### AHMA (Assistive Health & Medicine Assistant)

A full‑stack assistant that helps with insurance PDF form processing, medicine reminders (Google Calendar), Todoist tasks, and caregiver wellbeing — powered by a multi‑agent router with a React + Flask app.

## Contents
- Overview and architecture
- Tech stack
- Folder hierarchy
- Prerequisites
- Environment variables
- Setup & run
  - Backend API
  - Frontend (React)
  - Agents (Router + sub‑agents)
  - PDF workflow
- Features (how to use)
- Agents and tools overview
- Git hygiene
- Troubleshooting

## Overview and architecture
- React frontend provides chat + widgets (PDF, Calendar, Todoist).
- Flask backend exposes routes for chat (router agent), calendar, Todoist, and PDF processing.
- Router agent dispatches to domain agents (medicine, appointments, todo, wellbeing) and PDF tools.
- PDF utilities extract fields, merge data, and autofill forms.

## Tech stack
- Frontend: React (CRA), react-markdown
- Backend: Flask, Flask‑CORS, python‑dotenv, Google API client
- Agents: strands Agents + tools, AWS Bedrock (LLM), Google Calendar API
- PDF: PyPDF2

## Folder hierarchy
```
clueless/
  backend/                 # Flask API server (all routes)
  frontend/                # React SPA
  pdf/                     # PDF utilities: extract/merge/autofill and sample data
  reminders_agent/         # Medicine, appointments, wellbeing agents
  tracking_agent/          # Todoist agent/tools
  insurance/               # Additional agent(s)
  med_images_test/         # Runtime medicine images (ignored in git)
  superagent_test.py       # Router agent + tools entry for CLI testing
  README.md
```

Key files:
- backend/app.py: API routes for chat, calendar, todoist, pdf, and medicine images
- frontend/src/App.js: UI with chat, widgets, upload buttons
- superagent_test.py: Router agent and tools (medicine, appointment, todo, wellbeing + PDF)
- pdf/json_dump2.py, pdf/fetchdb.py, pdf/autofill.py: PDF workflow utilities

## Prerequisites
- Python 3.10+
- Node.js 18+
- npm 9+
- Conda (optional)
- Google Calendar credentials: `credentials.json` + generated `token.json`
- AWS credentials for Bedrock (environment or config chain)

## Environment variables
Create a `.env` in repo root (loaded by backend):
```
TODOIST_API_TOKEN=your_todoist_token
# Optional (if not using AWS default config chain)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```
Google credentials:
- Place `credentials.json` at repo root; first run will create `token.json`.

## Setup & run

### Backend API
```
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py   # http://localhost:5001
```

### Frontend (React)
```
cd frontend
npm install
npm start      # http://localhost:3000 (proxied to backend)
```

### Agents (Router + sub‑agents)
Router and tools live in `superagent_test.py` and import sub‑agents from `reminders_agent/` and `tracking_agent/`.
Optional CLI test:
```
python superagent_test.py
```

### PDF workflow
Utilities in `pdf/`:
- `json_dump2.py`: extract PDF fields to JSON
- `fetchdb.py`: fuzzy‑merge extracted fields with example JSON
- `autofill.py`: fill a PDF with values

Backend routes orchestrate extraction → merge → fill:
- `POST /api/pdf/upload` → upload into `backend/pdf_uploads`
- `POST /api/pdf/process` → run pipeline
- `GET /api/pdf/download/<filename>` → download filled PDF
- `GET /api/pdf/list` and `DELETE /api/pdf/delete/<filename>`

## Features (how to use)
- Insurance PDFs: In Insurance & PDF Forms widget → upload → process → download.
- Medicine photo → schedule → Calendar: Camera icon in chat uploads a photo; if not duplicate, backend triggers Medicine Agent to analyze and create Google Calendar events.
- Todoist: Frontend fetches Todoist tasks; you can add and complete tasks. Requires `TODOIST_API_TOKEN`.
- Calendar: Events fetched via Google Calendar API using your credentials.

## Agents and tools overview
- RouterAgent: routes to domain agents or PDF tools. Lives in `superagent_test.py`.
- MedicineAgent: reads medicine labels (`image_reader`), extracts schedules, calls `create_calendar_event`.
- AppointmentsAgent: creates general appointments in Google Calendar.
- TodoAgent: adds/completes Todoist tasks.
- WellbeingAgent: caregiver wellbeing guidance and scheduling.
- PDF Tools: `process_insurance_pdf`, `fill_health_declaration_form`, `fill_medical_claim_form`, `list_pdf_files`.

## Git hygiene
- Ignore runtime/build artifacts:
  - `med_images_test/`
  - `node_modules/`, `**/lib/`, `**/dist/`, `**/.cache/`, `**/.pack/`
  - `**/diagnosticMessages*.json`, `*.log`
- If any are already tracked, untrack once:
```
git rm -r --cached med_images_test node_modules
```

## Troubleshooting
- Port 3000 in use: answer “yes” to run on another port or stop the prior dev server.
- Todoist 501: set `TODOIST_API_TOKEN` in `.env`.
- Google errors: ensure `credentials.json` exists; delete `token.json` to re‑auth if needed.
- Medicine duplicates: backend uses SHA‑256 and cleans stale entries; deleting files then re‑uploading is supported.
- PDF field mismatches: use the smart workflow/data mapping in `pdf/`, or update example data JSON to match fields.
