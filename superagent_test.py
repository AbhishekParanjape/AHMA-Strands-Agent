from strands import Agent, tool
import boto3

from reminders_agent.medicine_agent import create_medicine_agent
from reminders_agent.appointments_agent import create_appointments_agent
from tracking_agent.todo_agent import create_todo_agent
from reminders_agent.wellbeing_agent import create_wellbeing_agent

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
    aws_secret_access_key="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"
)

# Create sub-agents
@tool
def medicine_agent(query: str) -> str:
    """
    This tool handles queries related to medicine reminders. 
    It forwards the query to the Medicine Agent and returns the response.
    Example: 'Remind me to take Amoxicillin at 9 AM tomorrow.'
    """
    agent = create_medicine_agent()
    return agent(query)

@tool
def appointment_agent(query: str) -> str:
    """
    This tool handles queries related to appointments. 
    It forwards the query to the Appointments Agent and returns the response, including a link to the google calendar event.
    Example: 'Schedule a meeting with John tomorrow at 3 PM.'
    """
    agent = create_appointments_agent()
    return agent(query)

@tool
def todo_agent(query: str) -> str:
    """
    This tool handles queries related to general to-do tasks.
    It forwards the query to the Todo Agent and returns the response.
    Example: 'Add water plants to my to-do list for tomorrow.'
    """
    agent = create_todo_agent()
    return agent(query)


@tool
def wellbeing_agent(query: str) -> str:
    """
    Handle caregiver wellbeing requests. 
    Can provide self-care advice, suggest resources, and schedule wellbeing activities. 
    """
    agent = create_wellbeing_agent()
    return wellbeing_agent(query)

# Router agent
router_agent = Agent(
    name="RouterAgent",
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt=(
        "You are a routing agent. Decide whether a user request is about:\n"
        "- Medicine spcific details, like name and frequency (send to MedicineAgent)\n"
        "- Calendar Appointments (send to AppointmentAgent)\n"
        "- General to-do tasks, usually including verbs (send to TodoistAgent)\n"
        "- Caregiver wellbeing (self-care, stress, resources) (send to WellbeingAgent)\n"
        "- If unsure, confirm with the user on which function they would like to use."
        "Forward the request to the correct agent and return their response."
    ),
    tools=[medicine_agent, appointment_agent, todo_agent, wellbeing_agent]
)

# ---------- Example usage ----------
'''user_message1 = "Please remind me to take Amoxicillin three times a day for 7 days."
response1 = router_agent(user_message1)
print("user 1:", response1)

user_message2 = "Book a lunch with Sarah tomorrow at 12 at Marina Bay Sands."
response2 = router_agent(user_message2)
print("user 2:", response2)'''

"""user_message3 = "Add a todo: water the plants tomorrow morning."
response3 = router_agent(user_message3)
print("user 3:", response3)
"""

user_message3 = "Collect the medicine from the doctors at 9am 30 sept 2025, in singapore."

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("👋 Goodbye!")
        break

    response3 = router_agent(user_input)
    print("Assistant:", response3)
