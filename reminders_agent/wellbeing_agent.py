def create_wellbeing_agent():
    from strands import Agent, tool
    from strands_tools import image_reader, current_time
    import boto3
    import os 

    from .google_event import create_event
    from tracking_agent.todoist_task import add_task_to_todoist

    # Bedrock client (credentials already set)
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
        aws_secret_access_key="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"
    )

    @tool
    def create_calendar_event(
        summary: str,
        start_time: str,
        end_time: str,
        location: str = None,
        description: str = None,
        recurrence: str = None,
    ) -> str:
        """
        Create a Google Calendar event, useful for scheduling wellbeing breaks or caregiver support calls.

        Args:
            summary: Title of the event.
            start_time: ISO datetime string, e.g. "2025-09-05T10:00:00+08:00".
            end_time: ISO datetime string.
            location: Optional location string.
            description: Optional description string.
            recurrence: Optional RRULE string, e.g. "RRULE:FREQ=DAILY;COUNT=10".

        Returns:
            The Google Calendar event link.

        Notes:
            - If recurrence is not provided, assume a single event.
            - Use RFC 5545 RRULE syntax for recurrence.
            - Default timezone: Asia/Singapore.
        """
        return create_event(summary, start_time, end_time, location, description, recurrence)


    @tool
    def create_todoist_task(
        task_name: str,
        task_due: str = None,
        priority: int = None,
        labels: list = None,
    ) -> str:
        """
        Create a wellbeing-related Todoist task.

        This tool is specifically for caregiver wellbeing and self-care tracking. 
        Use it when the caregiver wants to *build healthy habits, manage stress, or remember self-care activities*.
        Examples:
        - "Remind me to drink water every 2 hours"
        - "Add a daily gratitude journal task at night"
        - "Track exercise three times a week"
        - "Set a task for deep breathing breaks tomorrow at 10 AM and 3 PM"

        Args:
            task_name (str): Clear name of the task, e.g. "Hydrate", "Evening Walk", "Journal Entry".
            task_due: Optional due date in natural language format (e.g. "tomorrow at 9 AM").
            priority (int, optional): Task urgency (1 = highest, 4 = lowest).
                - Use priority 1–2 for critical wellbeing activities (e.g., "Take medication", "Sleep at least 7h").
                - Use priority 3–4 for softer habits (e.g., journaling, mindfulness).
            labels (list, optional): List of wellbeing-related labels, e.g.
                - ["self-care", "exercise"]
                - ["hydration", "daily"]
                - ["mental health"]

        Returns:
            str: Success or error message from Todoist.

        Notes for the model:
            - Use this tool instead of `create_calendar_event` for *ongoing habits or personal tasks*.
            - If the activity is time-bound (e.g., therapy session, scheduled call), prefer `create_calendar_event`.
            - Default to daily recurrence if the caregiver describes a *routine wellbeing habit*.
            - Always confirm with the user before scheduling recurring tasks.
        """
        return add_task_to_todoist(task_name, task_due, priority, labels)

    wellbeing_agent = Agent(
        name="WellbeingAgent",
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        system_prompt="""
        You are a caregiver wellbeing assistant. 
        Your role is to:
        - Provide stress-management, self-care, and mental health tips for caregivers. 
        - If needed, suggest local or online resources, support groups, respite care, or hotlines.
        - If the caregiver mentions needing a block of rest time, personal time or self-care, 
        or clearly wants professional help (e.g. therapy session, support group), delegate to the Appointments Agent. 
        - If they want to track tasks (e.g. "meditation", "exercise"), use the `create_todoist_task` tool. 
        Always explain what you’re doing, and confirm before creating an appointment.
        """,
        tools=[create_calendar_event, create_todoist_task] 
    )

    return wellbeing_agent

def test_agent():
    agent = create_wellbeing_agent()
    message = """
    I am feeling quite stressed now, just spent 4 hours taking care of my mom. I want to call a helpline later in the afternoon, maybe 4pm.
    """

    agent(message)

    while True:
        user_input = input("\n\nYou: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break

        response = agent(user_input)

# test_agent()  # Commented out to prevent interactive loop