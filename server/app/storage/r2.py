from __future__ import annotations

from dataclasses import dataclass

import boto3
from botocore.config import Config

from app.core.config import get_settings


@dataclass(frozen=True)
class PresignedUpload:
    object_key: str
    upload_url: str
    file_url: str

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


def presign_put_object(*, object_key: str, content_type: str) -> PresignedUpload:
    settings = get_settings()
    if not settings.r2_bucket_name:
        raise RuntimeError("R2 bucket not configured")

    client = _get_r2_client()
    upload_url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.r2_bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.r2_presign_expires_seconds,
    )

    if settings.r2_public_base_url:
        file_url = f"{settings.r2_public_base_url.rstrip('/')}/{object_key}"
    else:
        # Fallback: not necessarily publicly readable; still a stable reference.
        file_url = f"s3://{settings.r2_bucket_name}/{object_key}"

    return PresignedUpload(object_key=object_key, upload_url=upload_url, file_url=file_url)
