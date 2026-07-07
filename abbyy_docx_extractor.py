import json
import os
import docx
from collections import defaultdict
from docx.oxml.ns import qn
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
import pythoncom
from win32com.client import Dispatch

wdStatisticPages = 2
wdActiveEndPageNumber = 3
wdHorizontalPositionRelativeToPage = 5
wdVerticalPositionRelativeToPage = 6
wdMainTextStory = 1

# Open XML использует EMU (English Metric Units): 1 дюйм = 914400 EMU, 1 см = 360000 EMU.
EMU_PER_CM = 360000
EMU_PER_INCH = 914400
# 1 дюйм = 1440 твипов.
TWIPS_PER_CM = 567

def process_docx_file(filename):
    """
    Основная функция для обработки DOCX файла.
    """
    try:
        word = None
        pythoncom.CoInitialize()
        try:
            word = Dispatch("Word.Application")
            word.Visible = False

            doc = word.Documents.Open(os.path.abspath(filename))
            doc.Range().ListFormat.ConvertNumbersToText()

            num_pages = doc.ComputeStatistics(wdStatisticPages)
            print(f"Документ содержит {num_pages} страниц.")

            pages_data = defaultdict(lambda: {"blocks": []})

            for para in doc.Paragraphs:
                # Пропускаем текстовые рамки, колонтитулы и т.п. - не основной текст.
                if para.Range.StoryType != wdMainTextStory:
                    continue

                text = para.Range.Text.strip()
                if not text:
                    continue

                page_num = para.Range.Information(wdActiveEndPageNumber)
                page_setup = para.Range.PageSetup
                page_w_pt = page_setup.PageWidth
                page_h_pt = page_setup.PageHeight

                try:
                    x_pt = para.Range.Information(wdHorizontalPositionRelativeToPage)
                    y_pt = para.Range.Information(wdVerticalPositionRelativeToPage)
                    # Ширина/высота - аппроксимация, точных границ блока Word не даёт.
                    w_pt = page_w_pt - para.LeftIndent - para.RightIndent
                    h_pt = para.SpaceAfter + para.SpaceBefore + para.LineSpacing
                except Exception:
                    # Не удалось получить координаты (например, для пустых строк).
                    continue

                pages_data[page_num]["blocks"].append({
                    "text": text,
                    "type": "text",
                    "bounding_rect": {
                        "x": (x_pt / page_w_pt) * 100 if page_w_pt > 0 else 0,
                        "y": (y_pt / page_h_pt) * 100 if page_h_pt > 0 else 0,
                        "width": (w_pt / page_w_pt) * 100 if page_w_pt > 0 else 0,
                        "height": (h_pt / page_h_pt) * 100 if page_h_pt > 0 else 0,
                    }
                })

            for shape in doc.Shapes:
                if not shape.TextFrame.HasText:
                    continue

                text_range = shape.TextFrame.TextRange
                text = text_range.Text.strip()
                if not text:
                    continue

                page_num = text_range.Information(wdActiveEndPageNumber)

                page_setup = text_range.PageSetup
                page_w_pt = page_setup.PageWidth
                page_h_pt = page_setup.PageHeight

                x_pt = shape.Left
                y_pt = shape.Top
                w_pt = shape.Width
                h_pt = shape.Height

                pages_data[page_num]["blocks"].append({
                    "text": text,
                    "type": "text",
                    "bounding_rect": {
                        "x": (x_pt / page_w_pt) * 100 if page_w_pt > 0 else 0,
                        "y": (y_pt / page_h_pt) * 100 if page_h_pt > 0 else 0,
                        "width": (w_pt / page_w_pt) * 100 if page_w_pt > 0 else 0,
                        "height": (h_pt / page_h_pt) * 100 if page_h_pt > 0 else 0,
                    }
                })
            
            # Не сохраняем изменения, сделанные ConvertNumbersToText - они нужны только для парсинга.
            doc.Close(SaveChanges=0)

            output_dir_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
            os.makedirs(output_dir_json, exist_ok=True)
            
            for page_num, page_data in sorted(pages_data.items()):
                json_filename = os.path.join(output_dir_json, f"page_{page_num}.json")
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=4)
                print(f"Сохранен файл: {json_filename}")

            print("\nОбработка завершена.")

        finally:
            if word:
                word.Quit()
            pythoncom.CoUninitialize()

    except FileNotFoundError:
        print(f"Ошибка: Файл '{filename}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_to_process = 'C:/Users/user/Documents/099_01.docx'
    process_docx_file(file_to_process)