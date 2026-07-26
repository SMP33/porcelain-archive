from __future__ import annotations

from typing import Optional


def translated_label(type_: str, value: str, translated: Optional[str]) -> str:
    """Отображаемая метка значения указателя: перевод, если он есть."""
    if type_ == "bool":
        return "Да" if value == "true" else "Нет"
    if type_ == "string":
        return value
    return translated or value
