#!/usr/bin/env python3
"""
Test script to verify Google Calendar and Todoist integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ahma_backend import GoogleCalendarService, TodoistService

def test_google_calendar():
    """Test Google Calendar connection"""
    print("🔍 Testing Google Calendar connection...")
    
    gcal = GoogleCalendarService()
    
    # Check if credentials file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("📝 Please download credentials.json from Google Cloud Console")
        print("🔗 Go to: https://console.cloud.google.com/")
        print("   1. Create a new project or select existing")
        print("   2. Enable Google Calendar API")
        print("   3. Create OAuth 2.0 credentials")
        print("   4. Download credentials.json")
        return False
    
    # Try to authenticate
    if gcal.authenticate():
        print("✅ Google Calendar authentication successful!")
        
        # Try to get events
        events = gcal.get_upcoming_events(5)
        if events:
            print(f"📅 Found {len(events)} upcoming events:")
            for event in events:
                print(f"   • {event['summary']} - {event['start']}")
        else:
            print("📅 No upcoming events found")
        return True
    else:
        print("❌ Google Calendar authentication failed!")
        return False

def test_todoist():
    """Test Todoist connection"""
    print("\n🔍 Testing Todoist connection...")
    
    todoist = TodoistService()
    
    # Try to get tasks
    tasks = todoist.get_tasks(5)
    if tasks:
        print(f"✅ Todoist connection successful!")
        print(f"📝 Found {len(tasks)} tasks:")
        for task in tasks:
            status = "✅" if task['completed'] else "⏳"
            print(f"   {status} {task['content']} (Priority: {task['priority']})")
        return True
    else:
        print("❌ Todoist connection failed!")
        print("🔑 Check your TODOIST_API_TOKEN in ahma_backend.py")
        return False

def main():
    """Run all tests"""
    print("🧪 AHMA Integration Test")
    print("=" * 50)
    
    gcal_ok = test_google_calendar()
    todoist_ok = test_todoist()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Google Calendar: {'✅ Working' if gcal_ok else '❌ Not Working'}")
    print(f"   Todoist: {'✅ Working' if todoist_ok else '❌ Not Working'}")
    
    if gcal_ok and todoist_ok:
        print("\n🎉 All integrations are working! You can start the backend server.")
    else:
        print("\n⚠️  Some integrations need to be fixed before starting the server.")

if __name__ == "__main__":
    main()

