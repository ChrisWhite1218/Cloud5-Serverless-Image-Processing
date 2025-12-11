import base64
import json
import logging
import os
import io
from pathlib import Path

import boto3
from ai_helper import generate_image

def download_json_from_s3(bucket, key): # dowloads json prompt from s3
    s3 = boto3.client('s3')
    buffer = io.BytesIO()
    s3.download_fileobj(bucket, key, buffer)
    buffer.seek(0)
    return json.loads(buffer.read().decode())

def upload_to_s3(bucket, key, data, content_type='image/png'): # uploads ai image bytes to s3
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)

def ensure_openai_key():
    """Ensure OPENAI_API_KEY is set, fallback to Secrets Manager if provided."""
    if os.getenv("OPENAI_API_KEY"):
        return
    secret_name = os.getenv("OPENAI_API_SECRET_NAME")
    if not secret_name:
        raise RuntimeError("OPENAI_API_KEY missing and OPENAI_API_SECRET_NAME not set.")
    region_name = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client("secretsmanager", region_name=region_name)
    resp = client.get_secret_value(SecretId=secret_name)
    if "SecretString" in resp:
        os.environ["OPENAI_API_KEY"] = resp["SecretString"]
    else:
        os.environ["OPENAI_API_KEY"] = resp["SecretBinary"].decode("utf-8")

def api_handler(event, context):
    """
    Lambda parses the prompt, calls the AI image-generation API, stores the resulting image in processed/ai/, and logs prompt metadata.
    """
    ensure_openai_key()
    print("AI Image Lambda triggered")
    print(f"Event received with {len(event.get('Records', []))} SNS records")

    processed_count = 0
    failed_count = 0

    logger = logging.getLogger()

    # iterate over all SNS records
    for sns_record in event.get('Records', []):
        try:
            # extract and parse SNS message
            sns_message = json.loads(sns_record['Sns']['Message'])

            # iterate over all S3 records in the SNS message
            for s3_event in sns_message.get('Records', []):
                try:
                    s3_record = s3_event['s3']
                    bucket_name = s3_record['bucket']['name']
                    object_key = s3_record['object']['key']

                    print(f"Processing JSON prompt: s3://{bucket_name}/{object_key}")

                    # download prompt from S3
                    JSONprompt = download_json_from_s3(bucket_name, object_key)
                    prompt = JSONprompt.get("prompt")

                    # generate AI image based on prompt
                    result = generate_image(prompt)
                   
                    # upload result image bytes to /processed/ai/
                    filename = Path(object_key).name
                    output_key = f"processed/ai/{filename}"
                    upload_to_s3(bucket_name, output_key, result.image_bytes)
                    print(f"Uploaded to: {output_key}")

                    # save metadata 
                    metadata = {
                        "prompt": result.prompt, 
                        "model": result.model, 
                        "size": result.size, 
                        "duration_ms": result.metadata.get("duration_ms"), 
                        "request_id": result.metadata.get("request_id"), 
                        "seed": result.seed,
                    }
                    # save revised prompt if present
                    if result.revised_prompt:
                       metadata["revised_prompt"] = result.revised_prompt

                    # Log metadata
                    logger.info("Metadata: %s", metadata)
                    
                    processed_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to process {object_key}: {str(e)}"
                    print(error_msg)

        except Exception as e:
            print(f"Failed to process SNS record: {str(e)}")
            failed_count += 1

    summary = {
        'statusCode': 200 if failed_count == 0 else 207,  # @note: 207 = multi-status
        'processed': processed_count,
        'failed': failed_count,
    }

    print(f"Processing complete: {processed_count} succeeded, {failed_count} failed")
    return summary


def http_handler(event, context):
    """
    HTTP entrypoint (e.g., Lambda Function URL / API Gateway).
    Expects JSON body: {"prompt": "<text>"}.
    Returns JSON: {"image_base64": "...", "metadata": {...}}.
    """
    try:
        ensure_openai_key()
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Missing API key: {exc}"}),
        }

    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "prompt is required"}),
        }

    try:
        result = generate_image(prompt)
        image_b64 = base64.b64encode(result.image_bytes).decode("utf-8")
        metadata = {
            "prompt": result.prompt,
            "model": result.model,
            "size": result.size,
            "duration_ms": result.metadata.get("duration_ms"),
            "request_id": result.metadata.get("request_id"),
            "seed": result.seed,
        }
        if result.revised_prompt:
            metadata["revised_prompt"] = result.revised_prompt

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "image_base64": image_b64,
                    "metadata": metadata,
                }
            ),
        }
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }


def main_handler(event, context):
    """
    Router: if the event looks like SNS/S3 (Records with Sns), use api_handler;
    otherwise treat as HTTP and use http_handler.
    """
    records = event.get("Records")
    if records and isinstance(records, list):
        first = records[0]
        if isinstance(first, dict) and "Sns" in first:
            return api_handler(event, context)
    return http_handler(event, context)