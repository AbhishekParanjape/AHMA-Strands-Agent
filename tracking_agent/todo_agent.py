def create_todo_agent():
    from strands import Agent, tool
    import boto3
    from .todoist_task import add_task_to_todoist

    # Bedrock client (credentials already set)
    bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
        aws_secret_access_key="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"
    )

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
    agent = Agent(
        name="TodoistAgent",
        tools=[create_todoist_task],
        system_prompt=(""" You are a task management assistant.
    When the user talks about to-do items, chores, or tasks, create a Todoist task for them."""
        )
    )
    
    return agent

'''# Example usage: adding a task
task_input = "Give medication at 9 AM priority 1 it is urgent"
response = agent(prompt=task_input)
print(response)
'''
