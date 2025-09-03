# how the Google Calendar API works, using create_event function
# strands to fill in the arguments 
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def create_event(summary, start_time, end_time, location=None, description=None):
    service = get_calendar_service()

    event = {
        'summary': summary,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Singapore'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Singapore'},
    }

    if location:
        event['location'] = location
    if description:
        event['description'] = description

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get('htmlLink')