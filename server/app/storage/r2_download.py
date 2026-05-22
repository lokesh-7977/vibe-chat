from __future__ import annotations

import io
from urllib.parse import urlparse

import boto3
from botocore.config import Config
import httpx

from app.core.config import get_settings


def _get_r2_client():
    settings = get_settings()
    if not (settings.r2_endpoint_url and settings.r2_access_key_id and settings.r2_secret_access_key):
        raise RuntimeError("R2 settings not configured")

    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def download_document_bytes(file_url: str) -> bytes:
    """
    Supports:
    - public http(s) URLs (caller should fetch separately)
    - s3://bucket/key URLs pointing to R2 (download via S3 API)
    """
    if file_url.startswith("s3://"):
        parsed = urlparse(file_url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        client = _get_r2_client()
        obj = client.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()
        return body

    if file_url.startswith("http://") or file_url.startswith("https://"):
        resp = httpx.get(file_url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.content

    raise RuntimeError("Unsupported document URL for server-side download")
