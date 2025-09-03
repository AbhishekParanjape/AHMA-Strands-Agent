import os
import sys
import json
import time
import random

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Local imports
import utility

# Print SDK versions
print(f"Python version: {sys.version.split()[0]}")
print(f"Boto3 SDK version: {boto3.__version__}")

# Create boto3 session and set AWS region
boto_session = boto3.Session()
aws_region = boto_session.region_name

# Create boto3 clients for AOSS, Bedrock, and S3 services
aoss_client = boto3.client('opensearchserverless')
bedrock_agent_client = boto3.client('bedrock-agent')
s3_client = boto3.client('s3')

# Define names for AOSS, Bedrock, and S3 resources
resource_suffix = random.randrange(100, 999)
s3_bucket_name = f"bedrock-kb-{aws_region}-{resource_suffix}"
aoss_collection_name = f"bedrock-kb-collection-{resource_suffix}"
aoss_index_name = f"bedrock-kb-index-{resource_suffix}"
bedrock_kb_name = f"bedrock-kb-{resource_suffix}"

# Set the Bedrock model to use for embedding generation
embedding_model_id = 'amazon.titan-embed-text-v2:0'
embedding_model_arn = f'arn:aws:bedrock:{aws_region}::foundation-model/{embedding_model_id}'
embedding_model_dim = 1024

# Some temporary local paths
local_data_dir = 'data'

# Print configurations
print("AWS Region:", aws_region)
print("S3 Bucket:", s3_bucket_name)
print("AOSS Collection Name:", aoss_collection_name)
print("Bedrock Knowledge Base Name:", bedrock_kb_name)


try:
    s3_client.head_bucket(Bucket=s3_bucket_name)
    print(f"Bucket '{s3_bucket_name}' already exists..")
except ClientError as e:
    print(f"Creating bucket: '{s3_bucket_name}'..")
    if aws_region == 'us-east-1':
        s3_client.create_bucket(Bucket=s3_bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=s3_bucket_name,
            CreateBucketConfiguration={'LocationConstraint': aws_region}
        )

from urllib.request import urlretrieve

# adding sample text files to the S3 bucket

txtfiles_dir = os.path.join(os.path.dirname(__file__), 'txtfiles')

for root, _, files in os.walk(txtfiles_dir):
    for file in files:
        if file.endswith('.txt'):  # Only upload .txt files
            full_path = os.path.join(root, file)
            s3_client.upload_file(full_path, s3_bucket_name, file)
            print(f"Uploaded: '{file}' to 's3://{s3_bucket_name}'..")

bedrock_kb_execution_role = utility.create_bedrock_execution_role(bucket_name=s3_bucket_name)
bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']

print("Created KB execution role with ARN:", bedrock_kb_execution_role_arn)

# Create AOSS policies for the new vector collection
aoss_encryption_policy, aoss_network_policy, aoss_access_policy = utility.create_policies_in_oss(
    vector_store_name=aoss_collection_name,
    aoss_client=aoss_client,
    bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn)

print("Created encryption policy with name:", aoss_encryption_policy['securityPolicyDetail']['name'])
print("Created network policy with name:", aoss_network_policy['securityPolicyDetail']['name'])
print("Created access policy with name:", aoss_access_policy['accessPolicyDetail']['name'])

# Request to create AOSS collection
aoss_collection = aoss_client.create_collection(name=aoss_collection_name, type='VECTORSEARCH')

# Wait until collection becomes active
print("Waiting until AOSS collection becomes active: ", end='')
while True:
    response = aoss_client.list_collections(collectionFilters={'name': aoss_collection_name})
    status = response['collectionSummaries'][0]['status']
    if status in ('ACTIVE', 'FAILED'):
        print(" done.")
        break
    print('█', end='', flush=True)
    time.sleep(5)

print("An AOSS collection created:", json.dumps(response['collectionSummaries'], indent=2))

aoss_policy_arn = utility.create_oss_policy_attach_bedrock_execution_role(
    collection_id=aoss_collection['createCollectionDetail']['id'],
    bedrock_kb_execution_role=bedrock_kb_execution_role)

print("Waiting 60 sec for data access rules to be enforced: ", end='')
for _ in range(12):  # 12 * 5 sec = 60 sec
    print('█', end='', flush=True)
    time.sleep(5)
print(" done.")

print("Created and attached policy with ARN:", aoss_policy_arn)

from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection

# Use default credential configuration for authentication
credentials = boto_session.get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    aws_region,
    'aoss',
    session_token=credentials.token)

# Construct AOSS endpoint host
host = f"{aoss_collection['createCollectionDetail']['id']}.{aws_region}.aoss.amazonaws.com"

# Build the OpenSearch client
os_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

# Define the configuration for the AOSS vector index
index_definition = {
   "settings": {
      "index.knn": "true",
       "number_of_shards": 1,
       "knn.algo_param.ef_search": 512,
       "number_of_replicas": 0,
   },
   "mappings": {
      "properties": {
         "vector": {
            "type": "knn_vector",
            "dimension": embedding_model_dim,
             "method": {
                 "name": "hnsw",
                 "engine": "faiss",
                 "space_type": "l2"
             },
         },
         "text": {
            "type": "text"
         },
         "text-metadata": {
            "type": "text"
         }
      }
   }
}

# Create an OpenSearch index
response = os_client.indices.create(index=aoss_index_name, body=index_definition)

# Waiting for index creation to propagate
print("Waiting 30 sec for index update to propagate: ", end='')
for _ in range(6):  # 6 * 5 sec = 30 sec
    print('█', end='', flush=True)
    time.sleep(5)
print(" done.")

print("A new AOSS index created:", json.dumps(response, indent=2))

# Vector Storage Configuration
storage_config = {
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
        "collectionArn": aoss_collection["createCollectionDetail"]['arn'],
        "vectorIndexName": aoss_index_name,
        "fieldMapping": {
            "vectorField": "vector",
            "textField": "text",
            "metadataField": "text-metadata"
        }
    }
}

# Knowledge Base Configuration
knowledge_base_config = {
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
        "embeddingModelArn": embedding_model_arn
    }
}

response = bedrock_agent_client.create_knowledge_base(
    name=bedrock_kb_name,
    description="Amazon shareholder letter knowledge base.",
    roleArn=bedrock_kb_execution_role_arn,
    knowledgeBaseConfiguration=knowledge_base_config,
    storageConfiguration=storage_config)

bedrock_kb_id = response['knowledgeBase']['knowledgeBaseId']

print("Waiting until BKB becomes active: ", end='')
while True:
    response = bedrock_agent_client.get_knowledge_base(knowledgeBaseId=bedrock_kb_id)
    if response['knowledgeBase']['status'] == 'ACTIVE':
        print(" done.")
        break
    print('█', end='', flush=True)
    time.sleep(5)

print("A new Bedrock Knowledge Base created with ID:", bedrock_kb_id)

response = bedrock_agent_client.get_knowledge_base(knowledgeBaseId=bedrock_kb_id)

print(json.dumps(response['knowledgeBase'], indent=2, default=str))

# Data Source Configuration
data_source_config = {
        "type": "S3",
        "s3Configuration":{
            "bucketArn": f"arn:aws:s3:::{s3_bucket_name}",
            # "inclusionPrefixes":["*.*"]   # you can use this if you want to create a KB using data within s3 prefixes.
        }
    }

# Vector Ingestion Configuration
vector_ingestion_config = {
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 512,
                "overlapPercentage": 20
            }
        }
    }

response = bedrock_agent_client.create_data_source(
    name=bedrock_kb_name,
    description="Amazon shareholder letter knowledge base.",
    knowledgeBaseId=bedrock_kb_id,
    dataSourceConfiguration=data_source_config,
    vectorIngestionConfiguration=vector_ingestion_config
)

bedrock_ds_id = response['dataSource']['dataSourceId']

print("A new BKB data source created with ID:", bedrock_ds_id)

response = bedrock_agent_client.get_data_source(knowledgeBaseId=bedrock_kb_id, dataSourceId=bedrock_ds_id)

print(json.dumps(response['dataSource'], indent=2, default=str))


response = bedrock_agent_client.start_ingestion_job(knowledgeBaseId=bedrock_kb_id, dataSourceId=bedrock_ds_id)

bedrock_job_id = response['ingestionJob']['ingestionJobId']

print("A new BKB ingestion job started with ID:", bedrock_job_id)

# Wait until ingestion job completes
print("Waiting until BKB ingestion job completes: ", end='')
while True:
    response = bedrock_agent_client.get_ingestion_job(
        knowledgeBaseId = bedrock_kb_id,
        dataSourceId = bedrock_ds_id,
        ingestionJobId = bedrock_job_id)
    if response['ingestionJob']['status'] == 'COMPLETE':
        print(" done.")
        break
    print('█', end='', flush=True)
    time.sleep(5)

print("The BKB ingestion job finished:", json.dumps(response['ingestionJob'], indent=2, default=str))


