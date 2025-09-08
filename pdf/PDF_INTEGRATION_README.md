# PDF Integration with AHMA Frontend

## Overview
The PDF processing functionality has been integrated into the AHMA frontend insurance widget, allowing users to upload PDF forms, process them with AI-generated data, and download filled forms.

## Features

### Backend API Endpoints
- `POST /api/pdf/upload` - Upload PDF files
- `POST /api/pdf/process` - Process uploaded PDFs with form filling
- `GET /api/pdf/download/<filename>` - Download processed PDFs
- `GET /api/pdf/list` - List uploaded and processed PDFs
- `DELETE /api/pdf/delete/<filename>` - Delete PDF files

### Frontend Features
- **PDF Upload**: Drag & drop or click to upload PDF forms
- **Form Processing**: Automatic form type detection and data filling
- **File Management**: View uploaded and processed files
- **Download**: Download filled forms
- **Real-time Updates**: Live updates when files are processed

## How to Use

### 1. Upload a PDF
1. Click "Upload PDF Form" in the Insurance & PDF Forms widget
2. Select a PDF file from your computer
3. The file will be uploaded and appear in the "Uploaded Forms" section

### 2. Process the PDF
1. Click the "⚡ Process" button next to any uploaded PDF
2. The system will automatically detect the form type and fill it with appropriate data
3. The filled form will appear in the "✅ Filled Forms" section

### 3. Download the Filled Form
1. Click the "📥 Download" button next to any filled form
2. The PDF will be downloaded to your computer

## Supported Form Types

- **Health Declaration Forms**: Uses `health_example_data.json` for data
- **Medical Claim Forms**: Uses `example_data.json` for data
- **Auto-detection**: Automatically determines form type based on field names

## Technical Details

### Backend Structure
```
backend/
├── app.py                 # Main Flask app with PDF endpoints
├── pdf_uploads/          # Directory for uploaded PDFs
└── pdf_processed/        # Directory for filled PDFs
```

### Frontend Integration
- PDF functionality integrated into the existing insurance widget
- Uses React state management for file tracking
- Real-time updates via API calls
- Responsive design with modern UI

### Dependencies
- Flask with file upload support
- PDF processing scripts (json_dump2.py, fetchdb.py, autofill.py)
- React frontend with file handling

## Testing

Run the test script to verify the integration:
```bash
python test_pdf_integration.py
```

## File Structure
```
pdf/
├── json_dump2.py          # Extract PDF form fields
├── fetchdb.py             # Merge data with fields
├── autofill.py            # Fill PDF with data
├── example_data.json      # Sample data for medical claims
└── health_example_data.json # Sample data for health declarations

backend/
├── app.py                 # Flask backend with PDF endpoints
├── pdf_uploads/           # Uploaded PDF storage
└── pdf_processed/         # Processed PDF storage

frontend/src/
├── App.js                 # React app with PDF widget
└── App.css                # Styling for PDF components
```

## Error Handling
- File type validation (PDF only)
- Upload size limits
- Processing error messages
- Network error handling
- User-friendly error messages in chat

## Future Enhancements
- Batch processing of multiple PDFs
- Custom data input forms
- PDF preview functionality
- Integration with cloud storage
- Advanced form type detection
