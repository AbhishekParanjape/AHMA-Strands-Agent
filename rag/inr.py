import os
import sys
import json
import time

# Third-party imports
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Local imports
import utility

# Print SDK versions
print(f"Python version: {sys.version.split()[0]}")
print(f"Boto3 SDK version: {boto3.__version__}")


# Create boto3 session and set AWS region
boto_session = boto3.Session()
aws_region = boto_session.region_name

bedrock_kb_id = "SHABQHFGFW"
# Create boto3 clients for Bedrock
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client('bedrock-agent-runtime', config=bedrock_config)

# Set the Bedrock model to use for text generation
model_id = 'amazon.nova-micro-v1:0'
model_arn = f'arn:aws:bedrock:{aws_region}::foundation-model/{model_id}'

# Print configurations
print("AWS Region:", aws_region)
print("Bedrock Knowledge Base ID:", bedrock_kb_id)

"""print("Citations:\n", json.dumps(response["citations"], indent=2, default=str))"""

def retrieve(user_query, kb_id, num_of_results=5):
    return bedrock_agent_client.retrieve(
        retrievalQuery= {
            'text': user_query
        },
        knowledgeBaseId=kb_id,
        retrievalConfiguration= {
            'vectorSearchConfiguration': {
                'numberOfResults': num_of_results,
                'overrideSearchType': "HYBRID", # optional
            }
        }
    )

# Define a system prompt
system_prompt = """You are a financial advisor AI system, and provides answers to questions
by using fact based and statistical information when possible. 
Use the following pieces of information in <context> tags to provide a concise answer to the questions.
Give an answer directly, without any XML tags.
If you don't know the answer, just say that you don't know, don't try to make up an answer."""

# Define a user prompt template
user_prompt_template = """Here is some additional context:
<context>
{contexts}
</context>

Please provide an answer to this user query:
<query>
{user_query}
</query>

The response should be specific and use statistics or numbers when possible."""

response = retrieve(user_query, bedrock_kb_id, num_of_results=3)

# Extract all context from all relevant retrieved document chunks
contexts = [rr['content']['text'] for rr in response['retrievalResults']]

# Build Converse API request
converse_request = {
    "system": [
        {"text": system_prompt}
    ],
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "text": user_prompt_template.format(contexts=contexts, user_query=user_query)
                }
            ]
        }
    ],
    "inferenceConfig": {
        "temperature": 0.4,
        "topP": 0.9,
        "maxTokens": 500
    }
}

# Call Bedrock's Converse API to generate the final answer to user query
response = bedrock_client.converse(
    modelId=model_id,
    system=converse_request['system'],
    messages=converse_request["messages"],
    inferenceConfig=converse_request["inferenceConfig"]
)

print("Final Answer:\n", response["output"]["message"]["content"][0]["text"])