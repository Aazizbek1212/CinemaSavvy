#!/usr/bin/env python3
"""Simple MinIO / S3 smoke test.

Requires: `boto3` installed in the environment and Docker/MinIO running.

Usage:
  python scripts/smoke_minio.py

It reads `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` from environment variables.
"""
import os
import sys

try:
    import boto3
    from botocore.client import Config
except Exception:
    print('boto3 is required. Install with: pip install boto3')
    sys.exit(1)

endpoint = os.environ.get('MINIO_ENDPOINT', 'http://localhost:9000')
access = os.environ.get('MINIO_ACCESS_KEY')
secret = os.environ.get('MINIO_SECRET_KEY')

if not access or not secret:
    print('Set MINIO_ACCESS_KEY and MINIO_SECRET_KEY in environment (or source .env).')
    sys.exit(1)

s3 = boto3.resource(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1',
)

bucket_name = os.environ.get('MINIO_BUCKET_NAME', 'cinema')

print('Checking connectivity to', endpoint)
try:
    # Ensure bucket exists (create if not)
    bucket = s3.Bucket(bucket_name)
    if bucket.creation_date is None:
        print('Bucket not found — creating:', bucket_name)
        s3.create_bucket(Bucket=bucket_name)
    else:
        print('Bucket exists:', bucket_name)

    # Upload a small test object
    key = 'smoke-test.txt'
    body = b'hello-minio-smoke-test'
    print('Uploading test object...')
    bucket.put_object(Key=key, Body=body)

    print('Downloading test object...')
    obj = bucket.Object(key).get()
    content = obj['Body'].read()
    if content == body:
        print('Smoke test passed: upload/download OK')
    else:
        print('Smoke test failed: content mismatch')

    # Cleanup
    bucket.Object(key).delete()
    print('Cleanup done')
except Exception as exc:
    print('Smoke test error:', exc)
    sys.exit(2)
