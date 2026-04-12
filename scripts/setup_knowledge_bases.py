"""
One-time AWS provisioning script.
Creates three Bedrock Knowledge Bases backed by S3 and managed vector storage.

Usage:
    python scripts/setup_knowledge_bases.py

Prerequisites:
    - .env populated with AWS credentials and BEDROCK_KB_ROLE_ARN
    - S3 bucket already created (S3_BUCKET_NAME)
    - Source documents uploaded to:
        s3://<bucket>/advising/
        s3://<bucket>/finaid/
        s3://<bucket>/wellness/
"""
import boto3
import os
import time
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
ROLE_ARN = os.getenv("BEDROCK_KB_ROLE_ARN", "")
BUCKET = os.getenv("S3_BUCKET_NAME", "omnicampus-docs")

AGENT_CONFIGS = [
    {
        "name": "OmniCampus-Advising",
        "description": "CSU academic advising: catalog, major sheets, registration, GE policies",
        "s3_prefix": "advising/",
        "env_key": "KB_ADVISING_ID",
    },
    {
        "name": "OmniCampus-FinAid",
        "description": "CSU financial aid: FAFSA, Cal Grant, scholarships, SAP, emergency funds",
        "s3_prefix": "finaid/",
        "env_key": "KB_FINAID_ID",
    },
    {
        "name": "OmniCampus-Wellness",
        "description": "CSU student wellness: counseling, crisis resources, TimelyCare, mindfulness",
        "s3_prefix": "wellness/",
        "env_key": "KB_WELLNESS_ID",
    },
]


def create_knowledge_base(bedrock_agent, config: dict) -> str:
    print(f"\nCreating Knowledge Base: {config['name']} ...")

    response = bedrock_agent.create_knowledge_base(
        name=config["name"],
        description=config["description"],
        roleArn=ROLE_ARN,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": (
                    "arn:aws:bedrock:us-east-1::foundation-model/"
                    "amazon.titan-embed-text-v2:0"
                )
            },
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": os.getenv("OPENSEARCH_COLLECTION_ARN", ""),
                "vectorIndexName": config["name"].lower().replace("-", "_"),
                "fieldMapping": {
                    "vectorField": "embedding",
                    "textField": "text",
                    "metadataField": "metadata",
                },
            },
        },
    )

    kb_id = response["knowledgeBase"]["knowledgeBaseId"]
    print(f"  KB created: {kb_id}")

    # Wait for KB to be ACTIVE
    for _ in range(20):
        status = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        if status["knowledgeBase"]["status"] == "ACTIVE":
            break
        print("  Waiting for ACTIVE status...")
        time.sleep(10)

    # Create S3 data source
    print(f"  Creating data source from s3://{BUCKET}/{config['s3_prefix']} ...")
    bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name=f"{config['name']}-S3",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{BUCKET}",
                "inclusionPrefixes": [config["s3_prefix"]],
            },
        },
    )

    return kb_id


def main():
    if not ROLE_ARN:
        print("ERROR: BEDROCK_KB_ROLE_ARN is not set in .env")
        return

    bedrock_agent = boto3.client(
        "bedrock-agent",
        region_name=REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    results = {}
    for config in AGENT_CONFIGS:
        kb_id = create_knowledge_base(bedrock_agent, config)
        results[config["env_key"]] = kb_id
        print(f"  {config['env_key']}={kb_id}")

    print("\n\nAdd these to your .env file:")
    print("-" * 40)
    for key, val in results.items():
        print(f"{key}={val}")


if __name__ == "__main__":
    main()
