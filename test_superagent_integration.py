#!/usr/bin/env python3
"""
Test script for Superagent Backend Integration
This script tests the connection between the backend and superagent
"""

import requests
import json
import time

def test_backend_connection():
    """Test if the backend is running and responding"""
    try:
        response = requests.get('http://localhost:5001/api/ahma/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running!")
            print(f"   Assistant: {data.get('assistant_name')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:5001")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint with various messages"""
    test_messages = [
        "Hello, how are you?",
        "Remind me to take Amoxicillin at 9 AM tomorrow",
        "Schedule a meeting with John tomorrow at 3 PM",
        "Add water plants to my to-do list for tomorrow",
        "I need help with my wellbeing",
        "Fill up my health-declaration-form.pdf"
    ]
    
    print("\n🧪 Testing chat endpoint...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}: {message} ---")
        
        try:
            response = requests.post(
                'http://localhost:5001/api/ahma/chat',
                json={'message': message},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Response: {data.get('response', 'No response')[:100]}...")
                else:
                    print(f"❌ Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out (30s)")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Small delay between requests
        time.sleep(1)

def test_conversation_history():
    """Test the conversation history endpoint"""
    print("\n📚 Testing conversation history...")
    
    try:
        response = requests.get('http://localhost:5001/api/ahma/conversation', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                conversation = data.get('conversation', [])
                print(f"✅ Conversation history loaded: {len(conversation)} messages")
                
                # Show last few messages
                for msg in conversation[-3:]:
                    msg_type = msg.get('type', 'unknown')
                    timestamp = msg.get('timestamp', 'No timestamp')
                    if msg_type == 'user':
                        print(f"   User: {msg.get('user', 'No message')[:50]}...")
                    elif msg_type == 'assistant':
                        print(f"   Assistant: {msg.get('assistant', 'No message')[:50]}...")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting conversation history: {e}")

def main():
    """Run all tests"""
    print("🧪 Superagent Backend Integration Test")
    print("=" * 50)
    
    # Test 1: Backend connection
    if not test_backend_connection():
        print("\n❌ Backend is not running. Please start it first:")
        print("   python superagent_backend.py")
        print("   or")
        print("   ./start_superagent_backend.sh")
        return
    
    # Test 2: Chat endpoint
    test_chat_endpoint()
    
    # Test 3: Conversation history
    test_conversation_history()
    
    print("\n🎉 Testing completed!")
    print("\nTo test with the frontend:")
    print("1. Start the backend: python superagent_backend.py")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Open http://localhost:3000 in your browser")

if __name__ == "__main__":
    main()
