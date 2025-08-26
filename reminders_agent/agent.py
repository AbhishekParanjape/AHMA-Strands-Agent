from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl
from strands_tools import image_reader
import boto3

# Bedrock client (credentials already set)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AKIA5KCDYHD2U5DEBI6K",
    aws_secret_access_key="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"
)
agent = Agent(tools=[image_reader])

# Basic usage - read an image file
result = agent.tool.image_reader(image_path="/Users/heyyzel/Documents/Agentic AI Hackathon/clueless/med_images_test/medtest1.jpg")

message = """
How often should I take my medicine?
"""
agent(message)