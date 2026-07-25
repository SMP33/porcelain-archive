from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from porcelain_archive.config import config
from porcelain_archive.database import db

# Миниатюра карточки документа: preview (129x200) в карточке ~300px мылит,
# web (1300x2000) тяжёлый - промежуточный размер кешируется отдельно.
CARD_MAX_SIDE = 800
CARD_MAX_KB = 160


def _ensure_card_image(image_hash: str) -> Optional[bytes]:
    """Готовит (при необходимости) и читает кеш карточной миниатюры. Блокирующая."""
    from porcelain_archive.task.utils import compress_image

    cache_root = Path(config.files.cache_path)
    card_path = cache_root / "card" / f"{image_hash}.jpg"
    if not card_path.exists():
        source = cache_root / "web" / f"{image_hash}.jpg"
        if not source.exists():
            return None
        card_path.parent.mkdir(parents=True, exist_ok=True)
        compress_image(str(source), str(card_path), CARD_MAX_SIDE, CARD_MAX_KB)
    try:
        return card_path.read_bytes()
    except OSError:
        return None


class DocumentsService:
    async def get_card_thumb(self, document_id: int) -> Optional[bytes]:
        """Миниатюра первой страницы master-ветки видимого документа."""
        rows = await db.execute_read(
            """
            SELECT pg.image_hash
            FROM document d
            JOIN branch b ON b.document_id = d.id AND b.name = 'master'
            JOIN page pg ON pg.commit = b.last_commit AND pg.pos = 1
            WHERE d.id = %s AND d.is_visible = 1 AND d.deleted = 0
            """,
            (document_id,),
        )
        if not rows or not rows[0][0]:
            return None
        return await asyncio.to_thread(_ensure_card_image, rows[0][0])


documents_service = DocumentsService()
