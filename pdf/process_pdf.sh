#!/bin/bash
# Simple wrapper script for processing insurance PDFs

# Change to the script directory
cd "$(dirname "$0")"

# Run the Python script with all arguments
python3 process_insurance_pdf.py "$@"
