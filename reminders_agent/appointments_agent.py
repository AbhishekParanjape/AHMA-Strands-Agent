from __future__ import print_function
import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_event import create_event

from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl
from strands_tools import image_reader
import boto3
import os 
  
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
I have a doctors appointment tomorrow 3 september 2025 at 4pm at Changi General Hospital. 
"""
"""
If there is a technical issue in making a google calendar event, can you explain to me why and give me the debugging error?
"""

agent(message)