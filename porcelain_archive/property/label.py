from __future__ import annotations

from typing import Optional

# Указатели типа 'string', для которых перевод всё же выполняется - значение
# в них само по себе не для показа (например, логин), а перевод - то, что
# должно отображаться пользователю.
TRANSLATABLE_STRING_TAGS = {"loaded_by"}


def translated_label(type_: str, value: str, translated: Optional[str], tag: Optional[str] = None) -> str:
    """Отображаемая метка значения указателя: перевод, если он есть."""
    if type_ == "bool":
        return "Да" if value == "true" else "Нет"
    if type_ == "string" and tag not in TRANSLATABLE_STRING_TAGS:
        return value
    return translated or value
