# Function to add a task to Todoist
def add_task_to_todoist(task_name, task_due=None, priority=None, labels=None):
    import requests
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
    TODOIST_API_URL = 'https://api.todoist.com/rest/v2/tasks'
    
    if not TODOIST_API_TOKEN:
        return "Error: TODOIST_API_TOKEN not found in environment variables"

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
    