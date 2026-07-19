"""
Распознавание текста на изображении страницы через Tesseract OCR (pytesseract).

Требует установленный в системе Tesseract OCR (бинарник tesseract в PATH,
языковые пакеты rus и eng - на Ubuntu: apt install tesseract-ocr tesseract-ocr-rus).
"""

import json
import re
import shutil
import tempfile
from pathlib import Path

import pytesseract
from PIL import Image

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import *

if shutil.which("tesseract") is None:
    raise RuntimeError(
        "Tesseract OCR не найден в PATH. Установите его в системе "
        "(Ubuntu: apt install tesseract-ocr tesseract-ocr-rus; "
        "Windows: https://github.com/UB-Mannheim/tesseract/wiki) и убедитесь, "
        "что каталог с tesseract.exe добавлен в PATH."
    )

OCR_LANG = "rus"
OCR_TESS_CONFIG = "--oem 1 --psm 3"

# Пороги средней уверенности Tesseract (0-100) для итогового ocr_quality страницы:
# >= HIGH - "high", >= LOW - "low", иначе - "worst".
OCR_QUALITY_HIGH_THRESHOLD = 75
OCR_QUALITY_LOW_THRESHOLD = 40

# Конец блока - перенос слова по строке (2+ строчные буквы и дефис на конце).
_HYPHEN_END_RE = re.compile(r"[а-яё]{2,}-$")
# Начало блока - продолжение перенесённого слова (строчная буква).
_LOWERCASE_START_RE = re.compile(r"^[а-яё]")

# Минимальная доля перекрытия по горизонтали (от ширины более узкого блока),
# начиная с которой два блока считаются одной колонкой/абзацем, а не соседними
# по вертикали, но разными по смыслу областями (разные колонки, подпись и т.п.).
PARAGRAPH_HORIZONTAL_OVERLAP_THRESHOLD = 0.5


def _line_height(block: dict) -> float:
    """Средняя высота строки блока (bbox по вертикали / число строк в тексте)."""
    return (block["y1"] - block["y0"]) / (block["text"].count("\n") + 1)


def _gap_below_half_font(prev: dict, block: dict) -> bool:
    """Проверяет, что block идёт сразу под prev, а разрыв между ними меньше половины высоты шрифта на границе."""
    gap = block["y0"] - prev["y1"]
    if gap < 0:
        return False

    font_size = max(_line_height(prev), _line_height(block))
    return font_size > 0 and gap < font_size / 2


def _horizontally_overlapping(prev: dict, block: dict) -> bool:
    """Проверяет, что блоки существенно перекрываются по горизонтали (одна колонка, не соседние области)."""
    overlap = min(prev["x1"], block["x1"]) - max(prev["x0"], block["x0"])
    min_width = min(prev["x1"] - prev["x0"], block["x1"] - block["x0"])
    return min_width > 0 and overlap / min_width >= PARAGRAPH_HORIZONTAL_OVERLAP_THRESHOLD


def _merge_block_geometry(prev: dict, block: dict, width: int, height: int) -> None:
    """Обновляет bbox, confidence и rect prev после присоединения block (текст соединяется отдельно)."""
    prev["x0"] = min(prev["x0"], block["x0"])
    prev["y0"] = min(prev["y0"], block["y0"])
    prev["x1"] = max(prev["x1"], block["x1"])
    prev["y1"] = max(prev["y1"], block["y1"])

    confs = [c for c in (prev["confidence"], block["confidence"]) if c is not None]
    prev["confidence"] = round(sum(confs) / len(confs), 1) if confs else None

    prev["rect"] = {
        "x": round(prev["x0"] / width * 100, 2),
        "y": round(prev["y0"] / height * 100, 2),
        "width": round((prev["x1"] - prev["x0"]) / width * 100, 2),
        "height": round((prev["y1"] - prev["y0"]) / height * 100, 2),
    }


def _dehyphenate_blocks(blocks_out: list[dict], width: int, height: int) -> list[dict]:
    """
    Склеивает подряд идущие блоки, разорванные переносом слова по строкам:
    первый блок заканчивается на 2+ строчные буквы с дефисом, второй начинается
    со строчной буквы, а разрыв между низом первого и верхом второго меньше
    половины высоты шрифта на границе. Дефис при склейке убирается.
    """
    def should_merge(prev: dict, block: dict) -> bool:
        return (
            bool(_HYPHEN_END_RE.search(prev["text"]))
            and bool(_LOWERCASE_START_RE.match(block["text"]))
            and _gap_below_half_font(prev, block)
        )

    def merge(prev: dict, block: dict) -> None:
        prev["text"] = prev["text"][:-1] + block["text"]
        _merge_block_geometry(prev, block, width, height)

    return _merge_consecutive_blocks(blocks_out, should_merge, merge)


def _merge_paragraph_blocks(blocks_out: list[dict], width: int, height: int) -> list[dict]:
    """
    Склеивает подряд идущие блоки одного абзаца: разрыв между низом первого и
    верхом второго меньше половины высоты шрифта на границе, и блоки существенно
    перекрываются по горизонтали (одна колонка, а не соседние области/колонки).
    Текст соединяется через перенос строки.
    """
    def should_merge(prev: dict, block: dict) -> bool:
        return _gap_below_half_font(prev, block) and _horizontally_overlapping(prev, block)

    def merge(prev: dict, block: dict) -> None:
        prev["text"] = f"{prev['text']}\n{block['text']}"
        _merge_block_geometry(prev, block, width, height)

    return _merge_consecutive_blocks(blocks_out, should_merge, merge)


def _merge_consecutive_blocks(blocks_out: list[dict], should_merge, merge) -> list[dict]:
    """Проходит по блокам по порядку и склеивает подряд идущие пары, для которых should_merge(prev, block) верно."""
    merged: list[dict] = []
    for block in blocks_out:
        prev = merged[-1] if merged else None
        if prev is not None and should_merge(prev, block):
            merge(prev, block)
            continue
        merged.append(dict(block))

    for seq, block in enumerate(merged, start=1):
        block["seq"] = seq

    return merged


def recognize_page(image_path: Path) -> dict:
    """Распознаёт текст изображения, возвращает страницу с блоками (текст, bbox в px, rect в %,
    confidence) и итоговым ocr_quality ('high'/'low'/'worst'), выведенным из средней уверенности Tesseract."""
    with Image.open(image_path) as img:
        width, height = img.size
        data = pytesseract.image_to_data(
            img, lang=OCR_LANG, config=OCR_TESS_CONFIG, output_type=pytesseract.Output.DICT
        )

    blocks: dict[tuple, dict] = {}
    order: list[tuple] = []
    page_confs: list[float] = []

    for i, word in enumerate(data["text"]):
        word = word.strip()
        if not word:
            continue

        block_key = (data["block_num"][i], data["par_num"][i])
        left, top = data["left"][i], data["top"][i]
        right, bottom = left + data["width"][i], top + data["height"][i]

        if block_key not in blocks:
            blocks[block_key] = {
                "text": "", "x0": left, "y0": top, "x1": right, "y1": bottom,
                "confs": [], "_line": None,
            }
            order.append(block_key)

        block = blocks[block_key]
        line_key = data["line_num"][i]
        separator = "\n" if block["_line"] not in (None, line_key) else (" " if block["text"] else "")
        block["text"] += separator + word
        block["_line"] = line_key

        block["x0"] = min(block["x0"], left)
        block["y0"] = min(block["y0"], top)
        block["x1"] = max(block["x1"], right)
        block["y1"] = max(block["y1"], bottom)

        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if conf >= 0:
            block["confs"].append(conf)
            page_confs.append(conf)

    blocks_out = []
    for seq, key in enumerate(order, start=1):
        block = blocks[key]
        confs = block["confs"]
        blocks_out.append({
            "seq": seq,
            "text": block["text"],
            "confidence": round(sum(confs) / len(confs), 1) if confs else None,
            "x0": block["x0"], "y0": block["y0"], "x1": block["x1"], "y1": block["y1"],
            "rect": {
                "x": round(block["x0"] / width * 100, 2),
                "y": round(block["y0"] / height * 100, 2),
                "width": round((block["x1"] - block["x0"]) / width * 100, 2),
                "height": round((block["y1"] - block["y0"]) / height * 100, 2),
            },
        })

    blocks_out = _dehyphenate_blocks(blocks_out, width, height)
    blocks_out = _merge_paragraph_blocks(blocks_out, width, height)

    avg_confidence = sum(page_confs) / len(page_confs) if page_confs else 0
    if avg_confidence >= OCR_QUALITY_HIGH_THRESHOLD:
        ocr_quality = "high"
    elif avg_confidence >= OCR_QUALITY_LOW_THRESHOLD:
        ocr_quality = "low"
    else:
        ocr_quality = "worst"

    return {"width": width, "height": height, "blocks": blocks_out, "ocr_quality": ocr_quality}


branch_path = None
branch_id = None
branch_name = None
tmpdir = None

try:
    info = TaskInfo.from_stdin()

    start = info.data["start"]
    end = info.data["end"]
    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]

    branch_path = config.files.repos_branch_root + f"/{branch_name}"
    doc_path = branch_path + "/doc"

    out = run_git(branch_path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    repo_path = Path(str(out.stdout).strip() + "/../").resolve()

    image_files = {f.stem: f for f in list_position_files(branch_path, branch_name, "img")}

    tmpdir = tempfile.mkdtemp()
    for position in range(start, end + 1):
        image_file = image_files.get(str(position))
        if image_file is None:
            raise FileNotFoundError(f"Изображение для позиции {position} не найдено в ветке {branch_name}")

        src_path = Path(tmpdir) / image_file.name
        materialize_lfs_file(repo_path, branch_name, f"img/{image_file.name}", str(src_path))

        page = recognize_page(src_path)

        json_path = Path(f"{doc_path}/{position}.json")
        json_path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
        run_git(branch_path, "add", "--sparse", f"./doc/{position}.json")

    run_git(branch_path, "commit", "-m", f"text_from_image_{start}_{end}")

finally:
    if tmpdir is not None:
        shutil.rmtree(tmpdir, ignore_errors=True)
        log(f"Удалена временная папка: {tmpdir}")

    if branch_path is not None:
        remove_branch_trash(branch_path)
        regenerate_branch_cache(branch_path, branch_id, branch_name)
