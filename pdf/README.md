# Insurance PDF Processing Workflow

This directory contains a complete workflow for processing insurance PDFs automatically. The workflow extracts form fields from PDFs, merges them with example data, and fills the PDF with the merged values.

## Files

- `process_insurance_pdf_smart.py` - **Smart workflow script** with automatic form type detection (recommended)
- `process_insurance_pdf.py` - Basic workflow script (manual example data selection)
- `process_pdf.sh` - Simple shell wrapper script
- `json_dump2.py` - Extracts form fields from PDF to JSON
- `fetchdb.py` - Merges example data with extracted fields
- `autofill.py` - Fills PDF with merged data
- `example_data.json` - Sample data for medical/accident claim forms
- `health_example_data.json` - Sample data for health declaration forms

## Quick Start

### Using the Smart Workflow (Recommended):
```bash
# Activate your conda environment with dependencies
conda activate agent

# Process any PDF - automatically detects form type and uses appropriate data
python3 process_insurance_pdf_smart.py "health-declaration-statement.pdf"
python3 process_insurance_pdf_smart.py "Medical Accident Living TPD.pdf"

# Process with custom output name
python3 process_insurance_pdf_smart.py "any_form.pdf" "filled_output.pdf"

# Override with custom example data
python3 process_insurance_pdf_smart.py "any_form.pdf" --example-data "custom_data.json"

# Keep intermediate files for debugging
python3 process_insurance_pdf_smart.py "any_form.pdf" --keep-intermediate
```

### Using the Basic Workflow (Manual):
```bash
# Activate your conda environment with dependencies
conda activate agent

# Process a PDF with manual example data selection
python3 process_insurance_pdf.py "Medical Accident Living TPD.pdf" --example-data "example_data.json"
python3 process_insurance_pdf.py "health-declaration-statement.pdf" --example-data "health_example_data.json"

# Process with custom output name
python3 process_insurance_pdf.py "Medical Accident Living TPD.pdf" "filled_output.pdf"

# Keep intermediate files for debugging
python3 process_insurance_pdf.py "Medical Accident Living TPD.pdf" --keep-intermediate
```

### Using the shell wrapper:
```bash
# Make sure you're in the conda environment
conda activate agent

# Process a PDF (uses basic workflow)
./process_pdf.sh "Medical Accident Living TPD.pdf"
```

## Workflow Steps

1. **Extract Fields** (`json_dump2.py`): Extracts all form fields from the PDF and saves them as JSON
2. **Detect Form Type** (smart workflow only): Analyzes field names to determine if it's a health declaration or medical claim form
3. **Merge Data** (`fetchdb.py`): Matches and merges the extracted fields with appropriate example data
4. **Fill PDF** (`autofill.py`): Creates a new PDF with all the form fields filled

## Form Type Detection

The smart workflow automatically detects form types based on field names:

- **Health Declaration Forms**: Detected by keywords like "policy no", "nric", "surrender penalty", "reinstatement"
- **Medical/Accident Claim Forms**: Detected by keywords like "accident", "medical", "hospital", "diagnosis", "benefit"
- **Unknown Forms**: Falls back to the default example data

## Dependencies

- Python 3.6+
- PyPDF2
- boto3 (optional, for S3 integration)

## Example Data Format

The `example_data.json` file should contain key-value pairs where:
- Keys match (or are similar to) the field names in the PDF
- Values are the data to fill into those fields
- Boolean values are used for checkboxes
- String values are used for text fields

## Troubleshooting

- Make sure you're in the correct conda environment with dependencies installed
- Check that the PDF has fillable form fields (AcroForm)
- Use `--keep-intermediate` to debug field matching issues
- The script will show detailed matching information during processing

## Output

- **Filled PDF**: `{original_name}_filled.pdf` (or custom name if specified)
- **Intermediate files** (if `--keep-intermediate` is used):
  - `{original_name}_fields.json` - Extracted form fields
  - `{original_name}_values.json` - Merged field values
