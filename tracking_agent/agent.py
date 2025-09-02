from strands import Agent, tool
import boto3
import requests

# Bedrock client (credentials already set)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
    aws_secret_access_key="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"
)

TODOIST_API_TOKEN = '8b2d9c28b628938c50081c85dfe03490fae5a241'
TODOIST_API_URL = 'https://api.todoist.com/rest/v2/tasks'

# Function to add a task to Todoist
def add_task_to_todoist(task_name, task_due=None, priority=None, labels=None):
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
    }

    data = {
        'content': task_name,
    }

    # Include due date if provided
    if task_due:
        data['due_string'] = task_due  

    # Include priority if provided
    if priority:
        data['priority'] = priority 

    # Include labels if provided
    if labels:
        data['labels'] = labels

    # Make the API request to Todoist
    response = requests.post(TODOIST_API_URL, json=data, headers=headers)

    if response.status_code == 200:
        return f"Task '{task_name}' added successfully!"
    else:
        return f"Error: {response.status_code}, {response.text}"
    
# Strands agent tool to add tasks
@tool
def create_todoist_task(task_name: str, task_due: str = None, priority: int = None, labels: list = None) -> str:
    """
    Create a Todoist task.
    
    Args:
        task_name: Title of the task.
        task_due: Optional due date in natural language format (e.g. "tomorrow at 9 AM").
        priority: Optional priority of the task (1 = highest, 4 = lowest).
        labels: Optional list of labels to assign to the task eg.["urgent", "chores", "daily care"]
    
    Returns:
        A message indicating if the task was successfully created or if there was an error.
    """
    return add_task_to_todoist(task_name, task_due, priority, labels)

# Create the Strands agent
agent = Agent(tools=[create_todoist_task])

# Example usage: adding a task
task_input = "Give medication at 9 AM priority 1 it is urgent"
response = agent(prompt=task_input)
print(response)

