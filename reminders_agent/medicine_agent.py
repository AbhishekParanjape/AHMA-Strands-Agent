def create_medicine_agent():
    from strands import Agent, tool
    from strands_tools import image_reader, current_time
    import boto3
    import os 

    from reminders_agent.google_event import create_event

    # Bedrock client (credentials already set)
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
        aws_secret_access_key="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"
    )

    @tool
    def create_calendar_event(
        summary: str, start_time: str, end_time: str, location: str = None, description: str = None, recurrence: str = None) -> str:
        """
        Create a Google Calendar event, for repeating medicine reminders.
        
        Args:
            summary: Title of the event, including medicine name.
            start_time: ISO datetime string, e.g. "2025-09-05T10:00:00+08:00".
            end_time: ISO datetime string.
            location: Optional location string.
            description: Optional description string.
            recurrence: Optional RRULE string, e.g. "RRULE:FREQ=DAILY;COUNT=10" or "RRULE:FREQ=WEEKLY;BYDAY=MO,TH".
        
        Returns:
            The Google Calendar event link.

        Notes for the model:
            - If end time nor duration is provided, assume duration is 15 minutes.
            - If recurrence is not provided, try to infer if it is a recurring intake, e.g. daily. Else, make it a single event.
            - Use RFC 5545 RRULE syntax for recurrence.
            - If timezone is not provided, assume Asia/Singapore. 
            - If user does not specify when to start medicine, assume today. 
        """
        return create_event(summary, start_time, end_time, location, description, recurrence)

    agent = Agent(
        name="MedicineAgent",
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        tools=[image_reader, create_calendar_event, current_time],
        system_prompt="""
    You are a helpful medical assistant that helps the user manage their medicine schedule.  
    If the user asks about taking medicine but does not specify the exact time(s), you must **ask clarifying questions** (e.g., "At what time would you like to take your morning pill?").  
    If the medicine has to ben taken at the same time on consecutive days, set daily recurring events until the medicine is completed. 
    Once you have enough details (medicine name, time, frequency), call the `create_calendar_event` tool to create reminders.  
    If there are different medicines, make the respective events for it.
    Always confirm the schedule with the user before creating the event. 
    """
    )

    # Basic usage - read an image file
    for image in os.listdir("med_images_test"):
        result = agent.tool.image_reader(image_path="med_images_test/" + image)

    return agent

def test_med_agent():
    agent = create_medicine_agent()
    message = """
    When should I take my medicine this week, starting from 4th september 2025, until I finish it, 
    assuming my morning is 9am, afternoon 2pm, and evening 9pm?
    If there is a debugging issue with setting recurrence, tell me what it is.
    """

    agent(message)

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break

        response = agent(user_input)
        print("Assistant:", response)

test_med_agent()