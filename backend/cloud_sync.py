import os
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError


class S3Syncer:
    def __init__(self, access_key: str, secret_key: str, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def upload(self, local_path: str, s3_key: Optional[str] = None) -> str:
        """Upload file to S3, return public URL."""
        if s3_key is None:
            s3_key = f"photos/{Path(local_path).name}"

        self.client.upload_file(
            local_path,
            self.bucket,
            s3_key,
            ExtraArgs={"ContentType": _guess_content_type(local_path)},
        )
        return f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"

    def check_bucket(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except ClientError:
            return False


def _guess_content_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }.get(ext, "application/octet-stream")
