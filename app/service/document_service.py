import random
from typing import List, Dict, Any


class DocumentService:
    """
    Сервис для бизнес-логики, связанной с документами.
    Вся логика здесь - MOCK (заглушка).
    """

    def __init__(self):
        # --- Имитация базы данных ---
        # В реальном приложении эти данные будут поступать из базы данных
        self.mock_documents = [
            {"id": i, "name": f"Документ №{i}.docx", "author": f"Автор {i % 10}", "created_at": f"2023-10-{random.randint(1, 30):02d}"}
            for i in range(1, 789)  # Создадим 788 документов для примера
        ]

    def get_document_count(self) -> int:
        """
        Возвращает общее количество документов.
        """
        return len(self.mock_documents)

    def get_documents_paginated(self, offset: int = 0, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка документов для пагинации.

        :param offset: Смещение (сколько документов пропустить).
        :param limit: Количество документов для возврата.
        """
        return self.mock_documents[offset : offset + limit]
