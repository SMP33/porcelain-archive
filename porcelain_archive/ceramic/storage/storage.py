"""Хранилище файлов ceramic (обложки объектов и т.п.).

Бэкенд выбирается по config.files.ceramic_storage_backend:
- "local" - файлы пишутся под config.files.ceramic_local_root, публичный URL /files/<key>
  (nginx на проде или StaticFiles-mount /files локально отдаёт этот каталог);
- "s3"    - объект кладётся в бакет config.ceramics3.*, URL = public_base_url/<key>.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from porcelain_archive.config import config

FILES_URL_PREFIX = "/files"


class _LocalBackend:
    def __init__(self, root: str):
        self.root = root

    def save(self, data: bytes, key: str) -> None:
        path = Path(self.root) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key: str) -> None:
        try:
            (Path(self.root) / key).unlink()
        except FileNotFoundError:
            pass

    def url(self, key: str) -> str:
        return f"{FILES_URL_PREFIX}/{key}"


class _S3Backend:
    def __init__(self, cfg) -> None:
        import boto3

        self._client = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            aws_access_key_id=cfg.access_key_id,
            aws_secret_access_key=cfg.secret_access_key,
        )
        self._bucket = cfg.bucket_name
        self._base = cfg.public_base_url.rstrip("/")

    def save(self, data: bytes, key: str) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def url(self, key: str) -> str:
        return f"{self._base}/{key}"


class Storage:
    """Ленивая инициализация бэкенда (config читается при первом обращении)."""

    def __init__(self) -> None:
        self._backend = None

    @property
    def backend(self):
        if self._backend is None:
            if config.files.ceramic_storage_backend == "s3":
                self._backend = _S3Backend(config.ceramics3)
            else:
                self._backend = _LocalBackend(config.files.ceramic_local_root)
        return self._backend

    def save_image(self, data: bytes, ext: str, prefix: str = "covers") -> str:
        """Сохраняет байты изображения под уникальным ключом prefix/<uuid>.<ext>, возвращает ключ."""
        ext = ext.lower().lstrip(".") or "bin"
        key = f"{prefix}/{uuid.uuid4().hex}.{ext}"
        self.backend.save(data, key)
        return key

    def save_file(self, data: bytes, filename: str, prefix: str = "feedback") -> str:
        """Сохраняет произвольный файл (расширение берётся из имени), возвращает ключ."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        key = f"{prefix}/{uuid.uuid4().hex}.{ext}"
        self.backend.save(data, key)
        return key

    def delete(self, key: Optional[str]) -> None:
        if key:
            self.backend.delete(key)

    def url(self, key: Optional[str]) -> Optional[str]:
        return self.backend.url(key) if key else None

    @property
    def local_root(self) -> str:
        return config.files.ceramic_local_root


storage = Storage()
