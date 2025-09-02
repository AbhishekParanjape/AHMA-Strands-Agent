from __future__ import print_function
import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
#from google_event import create_event

from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl
from strands_tools import image_reader
import boto3
import os 

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
    
# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Bedrock client (credentials already set)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
    aws_secret_access_key="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"
)

@tool
def create_calendar_event(summary: str, start_time: str, end_time: str, location: str = None, description: str = None) -> str:
    """
    Create a Google Calendar event.
    
    Args:
        summary: Title of the event.
        start_time: ISO datetime string, e.g. "2025-09-05T10:00:00+08:00".
        end_time: ISO datetime string.
        location: Optional location string.
        description: Optional description string.
    
    Returns:
        The Google Calendar event link.
    """
    return create_event(summary, start_time, end_time, location, description)

agent = Agent(
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[create_calendar_event])

message = """
I have a doctors appointment tomorrow 3 september 2025 at 4pm at Changi General Hospital. If there is a technical issue in making a google calendar event, can you explain to me why and give me the debugging error?
"""

agent(message)