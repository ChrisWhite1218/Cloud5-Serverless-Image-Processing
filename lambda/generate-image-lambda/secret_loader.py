"""
Utility to fetch the OpenAI API key from AWS Secrets Manager.
"""

import boto3
from botocore.exceptions import ClientError


def load_openai_key(secret_name: str, region_name: str) -> str:
    """
    Fetch OPENAI_API_KEY from Secrets Manager.
    Raises ClientError if retrieval fails.
    """
    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    if "SecretString" in response:
        return response["SecretString"]
    # Fallback if stored as binary
    return response["SecretBinary"].decode("utf-8")

