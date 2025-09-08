def create_appointments_agent():
    from .google_event import create_event

    from strands import Agent, tool
    from strands_tools import current_time
    import boto3
    import os 
    import datetime
    
    # Bedrock client (credentials already set)
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        
       
    )

    @tool
    def create_calendar_event(summary: str, start_time: str, end_time: str, location: str = None, description: str = None, recurrence: str = None) -> str:
        """
        Create a Google Calendar event.
        
        Args:
            summary: Title of the event.
            start_time: ISO datetime string, e.g. "2025-09-05T10:00:00+08:00".
            end_time: ISO datetime string.
            location: Optional location string.
            description: Optional description string.
            recurrence: Optional RRULE string, e.g. "RRULE:FREQ=DAILY;COUNT=10" or "RRULE:FREQ=WEEKLY;BYDAY=MO,TH".
        
        Returns:
            The Google Calendar event link.

        Notes for the model:
            - If the user says "now", call the `current_time` tool to get the exact timestamp.
            - You may add offsets (e.g., +1 hour) using reasoning before calling this tool.
            - If recurrence is not provided, default to a single event.
            - Use RFC 5545 RRULE syntax for recurrence.
        """
        return create_event(summary, start_time, end_time, location, description, reccurence)

    @tool
    def parse_time_phrases(phrase: str) -> str:
        """
        Convert natural language time phrases like 'now', 'tomorrow at 5pm' or 'next monday 10am'
        into an ISO datetime string (YYYY-MM-DDTHH:MM:SS±HH:MM).
        Uses the current system time as reference.
        """
        import dateparser  # pip install dateparser
        dt = dateparser.parse(phrase)
        if not dt:
            return "Could not parse time"
        return dt.isoformat()

    agent = Agent(
        name="AppointmentsAgent",
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        tools=[create_calendar_event, parse_time_phrases, current_time])

    return agent

def test():
    agent = create_appointments_agent()

    message = """
    I want blueberries on my pancakes now. I want Eliana and Zoe to be there with me. At Cendana Buttery.
    """

    """
    I have a doctors appointment tomorrow 3 september 2025 at 4pm at Changi General Hospital. 
    """
    """
    If there is a technical issue in making a google calendar event, can you explain to me why and give me the debugging error?
    """

    agent(message)

# test()