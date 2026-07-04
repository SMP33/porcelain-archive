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

# Константы Word
wdStatisticPages = 2
wdActiveEndPageNumber = 3
wdHorizontalPositionRelativeToPage = 5
wdVerticalPositionRelativeToPage = 6
wdMainTextStory = 1
# Единицы измерения в Open XML - EMU (English Metric Units)
# 1 дюйм = 914400 EMU
# 1 см = 360000 EMU
EMU_PER_CM = 360000
EMU_PER_INCH = 914400
# 1 дюйм = 1440 твипов (Twips)
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
            word.Visible = False # Работаем в фоновом режиме

            # Открываем документ и конвертируем номера списков в текст
            doc = word.Documents.Open(os.path.abspath(filename))
            doc.Range().ListFormat.ConvertNumbersToText()

            num_pages = doc.ComputeStatistics(wdStatisticPages)
            print(f"Документ содержит {num_pages} страниц.")

            # Словарь для хранения данных по страницам
            pages_data = defaultdict(lambda: {"blocks": []})

            # Обработка обычных абзацев в основном тексте документа
            for para in doc.Paragraphs:
                # Пропускаем абзацы, которые не являются частью основного текста
                # (например, в текстовых рамках, колонтитулах и т.д.)
                if para.Range.StoryType != wdMainTextStory:
                    continue

                # Пропускаем абзацы, которые не являются частью основного текста
                # (например, в текстовых рамках, колонтитулах и т.д.)
                if para.Range.StoryType != wdMainTextStory:
                    continue

                text = para.Range.Text.strip()
                if not text:
                    continue

                # Получаем номер страницы и размеры
                page_num = para.Range.Information(wdActiveEndPageNumber)
                page_setup = para.Range.PageSetup
                page_w_pt = page_setup.PageWidth
                page_h_pt = page_setup.PageHeight

                # Получаем координаты абзаца в пунктах (points)
                try:
                    x_pt = para.Range.Information(wdHorizontalPositionRelativeToPage)
                    y_pt = para.Range.Information(wdVerticalPositionRelativeToPage)
                    # Расчет ширины и высоты - это аппроксимация
                    w_pt = page_w_pt - para.LeftIndent - para.RightIndent
                    h_pt = para.SpaceAfter + para.SpaceBefore + para.LineSpacing
                except Exception:
                    # Если координаты получить не удалось (например, для пустых строк),
                    # пропускаем этот блок, чтобы избежать ошибок.
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

            # Обработка всех фигур (текстовых рамок) в документе
            for shape in doc.Shapes:
                # Пропускаем фигуры без текстовой рамки
                if not shape.TextFrame.HasText:
                    continue

                text_range = shape.TextFrame.TextRange
                text = text_range.Text.strip()
                if not text:
                    continue

                # Получаем номер страницы для фигуры
                page_num = text_range.Information(wdActiveEndPageNumber)
                
                # Получаем размеры страницы, на которой находится фигура
                page_setup = text_range.PageSetup
                page_w_pt = page_setup.PageWidth
                page_h_pt = page_setup.PageHeight

                # Координаты и размеры фигуры в пунктах (points)
                x_pt = shape.Left
                y_pt = shape.Top
                w_pt = shape.Width
                h_pt = shape.Height

                # Добавляем блок в данные соответствующей страницы
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
            
            # Закрываем документ без сохранения изменений, сделанных ConvertNumbersToText
            doc.Close(SaveChanges=0)
            
            # Сохраняем JSON для каждой страницы
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
    # Замените 'your_document.docx' на путь к вашему файлу
    file_to_process = 'C:/Users/user/Documents/099_01.docx'
    process_docx_file(file_to_process)