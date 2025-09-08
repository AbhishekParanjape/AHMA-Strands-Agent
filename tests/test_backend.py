#!/usr/bin/env python3
"""
Simple test script to verify the backend API is working
"""

import requests
import json

def test_backend():
    base_url = "http://localhost:5001"
    
    print("🧪 Testing AHMA Backend API...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test chat endpoint
    try:
        test_message = "Hello, can you help me with my medicine reminders?"
        response = requests.post(
            f"{base_url}/api/ahma/chat",
            json={"message": test_message},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat test successful!")
            print(f"📝 User message: {test_message}")
            print(f"🤖 AHMA response: {data['response']}")
        else:
            print(f"❌ Chat test failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
    
    # Test calendar endpoint
    try:
        response = requests.get(f"{base_url}/api/google-calendar/events")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Calendar test: Found {len(data['events'])} events")
        else:
            print(f"❌ Calendar test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Calendar test failed: {e}")
    
    # Test todoist endpoint
    try:
        response = requests.get(f"{base_url}/api/todoist/tasks")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Todoist test: Found {len(data['tasks'])} tasks")
        else:
            print(f"❌ Todoist test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Todoist test failed: {e}")

if __name__ == "__main__":
    test_backend()

