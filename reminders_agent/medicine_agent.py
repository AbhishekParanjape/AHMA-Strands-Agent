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
agent = Agent(tools=[image_reader])

# Basic usage - read an image file
for image in os.listdir("med_images_test"):
    result = agent.tool.image_reader(image_path="med_images_test/" + image)

message = """
What is my medicine consumption schedule like?
"""

agent(message)