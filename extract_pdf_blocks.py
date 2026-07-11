"""
Извлечение последовательности текстовых блоков из PDF.

В отличие от .docx, PDF — это формат постраничной вёрстки: КАЖДЫЙ символ
на странице рисуется по явным координатам (x, y). Поэтому, в отличие от
docx, координаты есть у всего текста без исключений — и у обычного потока,
и у "рамок". Не нужно рендерить документ, всё уже в самом файле.

Иерархия, которую строит этот скрипт (через pdfminer.six):
  page -> block (LTTextBox, аналог "рамки"/абзаца, естественный порядок
                  чтения определяется layout-анализом pdfminer)
        -> line  (LTTextLine, строка внутри блока)

Координаты — в points (1/72 дюйма), система координат PDF: y растёт СНИЗУ
вверх (0,0 — левый нижний угол страницы). Если нужны "экранные" координаты
(y сверху вниз, как в изображении), используйте top_down_y0/top_down_y1 —
они уже посчитаны через page_height - y.
"""

import io
import itertools
import os
import sys
from PIL import Image
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTImage, LTTextContainer, LTChar, LTPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import open_filename


class _SequencedAggregator(PDFPageAggregator):
    """Аггрегатор макета, помечающий каждый символ порядковым номером появления в content stream."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._char_seq = itertools.count()

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        adv = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        last = self.cur_item._objs[-1]
        if isinstance(last, LTChar):
            last.seq = next(self._char_seq)
        return adv


def _line_font_size(line):
    """Наибольший размер шрифта символов строки (для оценки высоты строки на границе блоков)."""
    sizes = [obj.size for obj in line if isinstance(obj, LTChar)]
    return max(sizes) if sizes else None


def _boundary_font_size(prev, block):
    """Размер шрифта на границе двух блоков (конец первого, начало второго)."""
    sizes = [s for s in (prev.get("_last_line_size"), block.get("_first_line_size")) if s is not None]
    return max(sizes) if sizes else None


def _merge_block_into(prev, block):
    """Присоединяет block к prev: текст блока присоединяется с новой строки, bbox объединяется."""
    prev["text"] = f"{prev['text']}\n{block['text']}".strip()
    prev["x0"] = min(prev["x0"], block["x0"])
    prev["y0"] = min(prev["y0"], block["y0"])
    prev["x1"] = max(prev["x1"], block["x1"])
    prev["y1"] = max(prev["y1"], block["y1"])
    prev["top_down_y0"] = min(prev["top_down_y0"], block["top_down_y0"])
    prev["top_down_y1"] = max(prev["top_down_y1"], block["top_down_y1"])
    prev["_last_line_size"] = block.get("_last_line_size", prev.get("_last_line_size"))


def _merge_adjacent_blocks(blocks):
    """Объединяет идущие подряд блоки, если разрыв между низом первого и
    верхом второго меньше половины высоты шрифта на границе."""
    merged = []
    for block in blocks:
        if merged:
            prev = merged[-1]
            gap = prev["y0"] - block["y1"]
            font_size = _boundary_font_size(prev, block)
            if font_size is not None and 0 <= gap < font_size / 2:
                _merge_block_into(prev, block)
                continue
        merged.append(block)
    return merged


def _bbox_to_pct_rect(x0, y0, x1, y1, page_w, page_h):
    """
    Переводит bbox (points, PDF-координаты, y снизу вверх) в прямоугольник
    в процентах от размеров страницы, в экранных координатах (y сверху вниз) -
    так его можно наложить поверх изображения страницы независимо от её размера.
    """
    return {
        "x": round(x0 / page_w * 100, 2),
        "y": round((page_h - y1) / page_h * 100, 2),
        "width": round((x1 - x0) / page_w * 100, 2),
        "height": round((y1 - y0) / page_h * 100, 2),
    }


def _iter_images(element):
    """Рекурсивно обходит LTFigure в поисках вложенных LTImage."""
    if isinstance(element, LTImage):
        yield element
        return
    if hasattr(element, "__iter__"):
        for child in element:
            yield from _iter_images(child)


def _is_background_image(page_layout, image):
    """Проверяет, что изображение по своему bbox покрывает всю страницу —
    то есть является её фоном. Изображения, занимающие лишь часть страницы
    (штампы, вставки), фоном не считаются, независимо от их разрешения."""
    px0, py0, px1, py1 = page_layout.bbox
    ix0, iy0, ix1, iy1 = image.bbox
    return ix0 <= px0 + 1 and iy0 <= py0 + 1 and ix1 >= px1 - 1 and iy1 >= py1 - 1


def _iter_non_background_images(page_layout):
    """Перебирает изображения страницы, кроме фонового."""
    for element in page_layout:
        for image in _iter_images(element):
            if not _is_background_image(page_layout, image):
                yield image


def _save_image(image, path):
    """Сохраняет изображение в файл без сжатия (BMP)."""
    data = image.stream.get_data()
    with Image.open(io.BytesIO(data)) as im:
        im.convert("RGB").save(path, format="BMP")


def extract_sequence(pdf_path, images_dir=None):
    """Возвращает список страниц; на каждой странице — список текстовых
    блоков в порядке их добавления в содержимое PDF. Не фоновые изображения
    каждой страницы сохраняются без сжатия в images_dir (по умолчанию -
    папка рядом с pdf)."""
    pages_out = []

    if images_dir is None:
        images_dir = os.path.splitext(pdf_path)[0] + "_pages"

    resource_manager = PDFResourceManager()
    device = _SequencedAggregator(resource_manager, laparams=LAParams())
    interpreter = PDFPageInterpreter(resource_manager, device)

    with open_filename(pdf_path, "rb") as fp:
        for page_num, page in enumerate(PDFPage.get_pages(fp), start=1):
            interpreter.process_page(page)
            page_layout = device.get_result()
            assert isinstance(page_layout, LTPage)
            page_h = page_layout.height
            page_w = page_layout.width
            blocks_out = []

            image_paths = []
            for image_num, image in enumerate(_iter_non_background_images(page_layout), start=1):
                os.makedirs(images_dir, exist_ok=True)
                image_path = os.path.join(images_dir, f"page_{page_num}_image_{image_num}.bmp")
                _save_image(image, image_path)
                image_paths.append(image_path)

            for element in page_layout:
                if not isinstance(element, LTTextContainer):
                    continue  # пропускаем картинки, линии, фигуры и т.п.

                x0, y0, x1, y1 = element.bbox
                char_seqs = []
                line_sizes = []

                for line in element:
                    if not hasattr(line, "__iter__"):
                        continue
                    char_seqs.extend(
                        obj.seq for obj in line if isinstance(obj, LTChar) and hasattr(obj, "seq")
                    )
                    size = _line_font_size(line)
                    if size is not None:
                        line_sizes.append(size)

                blocks_out.append({
                    "order": min(char_seqs) if char_seqs else 0,
                    "text": element.get_text().strip(),
                    "x0": round(x0, 1), "y0": round(y0, 1),
                    "x1": round(x1, 1), "y1": round(y1, 1),
                    "top_down_y0": round(page_h - y1, 1),
                    "top_down_y1": round(page_h - y0, 1),
                    "_first_line_size": line_sizes[0] if line_sizes else None,
                    "_last_line_size": line_sizes[-1] if line_sizes else None,
                })

            blocks_out.sort(key=lambda b: b["order"])
            blocks_out = _merge_adjacent_blocks(blocks_out)
            for block_seq, block in enumerate(blocks_out, start=1):
                block["seq"] = block_seq
                del block["order"]
                block.pop("_first_line_size", None)
                block.pop("_last_line_size", None)
                block["rect"] = _bbox_to_pct_rect(
                    block["x0"], block["y0"], block["x1"], block["y1"], page_w, page_h
                )

            pages_out.append({
                "width": round(page_layout.width, 1),
                "height": round(page_h, 1),
                "images": image_paths,
                "blocks": blocks_out,
            })

    return pages_out


if __name__ == "__main__":
    import colorama
    colorama.just_fix_windows_console()

    COLOR_PAGE = "\033[36m"
    COLOR_BLOCK = "\033[32m"
    COLOR_BBOX = "\033[33m"
    RESET = "\033[0m"

    path = sys.argv[1] if len(sys.argv) > 1 else "example/2.pdf"
    for page_num, page in enumerate(extract_sequence(path), start=1):
        print(f"{COLOR_PAGE}=== Страница {page_num} ({page['width']}x{page['height']} pt) ==={RESET}")
        for block in page["blocks"]:
            print(f"  {COLOR_BLOCK}[block {block['seq']}]{RESET} "
                  f"{COLOR_BBOX}bbox=({block['x0']},{block['y0']})-({block['x1']},{block['y1']}){RESET}")
            for line in block["text"].split("\n"):
                print(f"      {line}")
