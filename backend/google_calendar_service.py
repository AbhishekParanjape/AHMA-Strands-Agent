"""
Google Calendar Service for AHMA Backend
Handles authentication and API calls to Google Calendar
"""

import os
import sys
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.service = None
        # Use absolute paths to avoid issues when running from different directories
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_file = os.path.join(project_root, 'credentials.json')
        self.token_file = os.path.join(project_root, 'token.json')
        
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            creds = None
            
            # Check if token file exists
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        print(f"❌ {self.credentials_file} not found!")
                        print("📝 Please download credentials.json from Google Cloud Console")
                        print("🔗 Go to: https://console.cloud.google.com/")
                        print("   1. Create a new project or select existing")
                        print("   2. Enable Google Calendar API")
                        print("   3. Create OAuth 2.0 credentials")
                        print("   4. Download credentials.json")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_upcoming_events(self, max_results=10):
        """Get upcoming events from Google Calendar including today's events"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Get start of today (00:00:00) to include today's events
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = today.isoformat() + 'Z'
            
            # Debug: print the time range we're querying
            print(f"🔍 Querying events from: {time_min}")
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for frontend
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'htmlLink': event.get('htmlLink', '')
                })
            
            return formatted_events
            
        except HttpError as error:
            print(f"❌ Calendar API error: {error}")
            return []
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    def create_event(self, summary, start_time, end_time, location=None, description=None):
        """Create a new calendar event"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Asia/Singapore',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Asia/Singapore',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                        {'method': 'popup', 'minutes': 5},
                    ],
                },
            }
            
            if location:
                event['location'] = location
            if description:
                event['description'] = description
            
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return event
            
        except HttpError as error:
            print(f"❌ Error creating event: {error}")
            return None
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            return None
    
    def is_authenticated(self):
        """Check if service is authenticated"""
        return self.service is not None
    
    def create_test_event_today(self):
        """Create a test event for today to verify the integration"""
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Create an event for today at 2 PM
            today = datetime.utcnow().replace(hour=14, minute=0, second=0, microsecond=0)
            start_time = today.isoformat() + 'Z'
            end_time = today.replace(hour=15, minute=0).isoformat() + 'Z'
            
            event = {
                'summary': 'AHMA Test Event - Today',
                'description': 'This is a test event created by AHMA to verify calendar integration',
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30},
                        {'method': 'popup', 'minutes': 5},
                    ],
                },
            }
            
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            print(f"✅ Test event created: {created_event.get('htmlLink')}")
            return created_event
            
        except Exception as e:
            print(f"❌ Error creating test event: {e}")
            return None
