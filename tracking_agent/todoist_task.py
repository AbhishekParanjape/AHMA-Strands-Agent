# Function to add a task to Todoist
def add_task_to_todoist(task_name, task_due=None, priority=None, labels=None):
    import requests
    
    TODOIST_API_TOKEN = '8b2d9c28b628938c50081c85dfe03490fae5a241'
    TODOIST_API_URL = 'https://api.todoist.com/rest/v2/tasks'

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
    