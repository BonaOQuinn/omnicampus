"""
Bedrock Knowledge Base client — wraps retrieve_and_generate for all agents.
"""
import boto3
from dotenv import load_dotenv
import os

load_dotenv()

MODEL_ARN = (
    "arn:aws:bedrock:us-east-1::foundation-model/"
    "anthropic.claude-haiku-4-5-20251001-v1:0"
)


def get_bedrock_client():
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def query_knowledge_base(
    kb_id: str,
    question: str,
    system_prompt: str = "",
    num_results: int = 5,
) -> dict:
    """
    Send a question to a Bedrock Knowledge Base and return
    {'answer': str, 'sources': list[str]}.
    """
    client = get_bedrock_client()

    config = {
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": kb_id,
            "modelArn": MODEL_ARN,
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {"numberOfResults": num_results}
            },
        },
    }

    if system_prompt:
        config["knowledgeBaseConfiguration"]["generationConfiguration"] = {
            "promptTemplate": {"textPromptTemplate": f"{system_prompt}\n\n$search_results$"}
        }

    try:
        response = client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration=config,
        )

        answer = response.get("output", {}).get("text", "No answer generated.")

        sources = []
        for citation in response.get("citations", []):
            for ref in citation.get("retrievedReferences", []):
                uri = ref.get("location", {}).get("s3Location", {}).get("uri", "")
                if uri and uri not in sources:
                    sources.append(uri)

        return {"answer": answer, "sources": sources}

    except Exception as exc:
        return {
            "answer": f"[Bedrock error] {exc}",
            "sources": [],
        }
