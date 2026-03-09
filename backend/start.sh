#!/bin/bash
# Start AHMA Backend

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Start Flask app
echo "🚀 Starting AHMA Backend on http://localhost:5001"
python3 app.py
