#!/usr/bin/env python3
"""
Test PDF integration with the backend
"""

import requests
import os
import json

def test_pdf_endpoints():
    """Test PDF processing endpoints."""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing PDF Integration...")
    
    # Test 1: List PDFs (should be empty initially)
    print("\n1. Testing list PDFs endpoint...")
    try:
        response = requests.get(f"{base_url}/api/pdf/list")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List PDFs: {data}")
        else:
            print(f"❌ List PDFs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List PDFs error: {e}")
    
    # Test 2: Upload a test PDF
    print("\n2. Testing PDF upload...")
    test_pdf_path = "pdf/health-declaration-statement.pdf"
    if os.path.exists(test_pdf_path):
        try:
            with open(test_pdf_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{base_url}/api/pdf/upload", files=files)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Upload successful: {data}")
                    filename = data.get('filename')
                    
                    # Test 3: Process the uploaded PDF
                    if filename:
                        print(f"\n3. Testing PDF processing...")
                        process_data = {
                            'filename': filename,
                            'form_type': 'health_declaration'
                        }
                        response = requests.post(
                            f"{base_url}/api/pdf/process",
                            json=process_data,
                            headers={'Content-Type': 'application/json'}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            print(f"✅ Processing successful: {data}")
                        else:
                            print(f"❌ Processing failed: {response.status_code} - {response.text}")
                else:
                    print(f"❌ Upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Upload error: {e}")
    else:
        print(f"❌ Test PDF not found: {test_pdf_path}")
    
    # Test 4: List PDFs again (should show uploaded and processed files)
    print("\n4. Testing list PDFs after processing...")
    try:
        response = requests.get(f"{base_url}/api/pdf/list")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Updated list: {data}")
        else:
            print(f"❌ List PDFs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List PDFs error: {e}")

if __name__ == "__main__":
    test_pdf_endpoints()
