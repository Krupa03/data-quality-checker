"""
Uploads a quality-check JSON report to S3 (LocalStack locally, or real AWS
if AWS_ENDPOINT_URL is unset / pointed at production).

Usage:
    python -m cli.main run --table fact_orders > report.json
    python cli/upload_report.py report.json
"""

import sys
from datetime import datetime, timezone

import boto3

BUCKET_NAME = "dq-checker-reports"
ENDPOINT_URL = "http://localhost:4566"  # LocalStack; remove/change for real AWS


def upload_report(local_path: str, bucket: str = BUCKET_NAME) -> str:
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    key = f"reports/{timestamp}-report.json"
    s3.upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cli/upload_report.py <path-to-report.json>")
        sys.exit(1)
    location = upload_report(sys.argv[1])
    print(f"Uploaded report to {location}")
