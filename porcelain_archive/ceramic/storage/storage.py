"""
Storage abstraction: local filesystem (dev) or S3-compatible (prod).

Usage:
    storage = get_storage()
    url = storage.public_url("documents/factory1/doc42/page_01.jpg")
    storage.upload("documents/factory1/doc42/page_01.jpg", image_bytes, "image/jpeg")
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config

from porcelain_archive.config import config


class StorageBackend(Protocol):
    def public_url(self, key: str) -> str: ...
    def upload(self, key: str, data: bytes, content_type: str) -> None: ...
    def download(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    """Stores files on the local filesystem. For development only."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def public_url(self, key: str) -> str:
        return f"/files/{key}"

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download(self, key: str) -> bytes:
        return (self.base_dir / key).read_bytes()

    def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()


class S3Storage:
    """S3-compatible storage: Cloudflare R2, MinIO, Yandex Object Storage, AWS S3."""

    def __init__(self) -> None:
        self.bucket = config.ceramics3.bucket_name
        self.public_base = config.ceramics3.public_base_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=config.ceramics3.endpoint_url or None,
            aws_access_key_id=config.ceramics3.access_key_id,
            aws_secret_access_key=config.ceramics3.secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def public_url(self, key: str) -> str:
        return f"{self.public_base}/{key}"

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def download(self, key: str) -> bytes:
        resp = self.client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> StorageBackend:
    if config.files.ceramic_storage_backend == "s3":
        return S3Storage()
    return LocalStorage(Path(config.files.ceramic_local_root or "./data/files"))
