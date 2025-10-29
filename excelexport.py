import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from config import config
from logger import logger


class ExcelExporter:
    def export_screenshots_to_excel(self, screenshots_folder, excel_path=None):
        """
        Экспортирует скриншоты по подпапкам.
        Каждая подпапка = отдельный лист Excel.
        """
        print("=== НАЧАЛО ЭКСПОРТА ===")

        try:
            # Получаем все подпапки, включая group_ папки
            subfolders = [
                f for f in os.listdir(screenshots_folder)
                if os.path.isdir(os.path.join(screenshots_folder, f)) and f.startswith('group_')
            ]
            
            if not subfolders:
                return None, "Нет подпапок для экспорта"

            subfolders.sort()
            print(f"Найдено подпапок: {len(subfolders)}")
            print(f"Подпапки: {subfolders}")

            # Создаём Excel
            if not excel_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_path = os.path.join(screenshots_folder, f"PreRun_{timestamp}.xlsx")

            workbook = Workbook()
            workbook.remove(workbook.active)  # удаляем дефолтный пустой лист

            total_screens = 0

            for subfolder in subfolders:
                sheet = workbook.create_sheet(title=subfolder)
                folder_path = os.path.join(screenshots_folder, subfolder)
                print(f"Создаю лист для {subfolder}")

                # Список файлов - ищем PNG и JPG
                files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    import glob
                    pattern = os.path.join(folder_path, f"screenshot_*{ext[1:]}")
                    found_files = glob.glob(pattern)
                    files.extend([os.path.basename(f) for f in found_files])
                
                # Альтернативный способ без glob
                if not files:
                    files = [
                        f for f in os.listdir(folder_path)
                        if (f.lower().endswith('.png') or f.lower().endswith('.jpg') or f.lower().endswith('.jpeg')) 
                        and f.startswith('screenshot_')
                    ]
                
                files.sort()
                print(f"В папке {subfolder} найдено файлов: {len(files)}")
                print(f"Файлы: {files}")

                current_row = 2

                for i, filename in enumerate(files, 1):
                    path = os.path.join(folder_path, filename)
                    created_time = datetime.fromtimestamp(os.path.getctime(path))
                    try:
                        img = ExcelImage(path)
                        img.anchor = f'A{current_row}'
                        sheet.add_image(img)

                        sheet.cell(row=current_row, column=2, value=filename)
                        sheet.cell(row=current_row, column=3,
                                   value=created_time.strftime('%Y-%m-%d %H:%M:%S'))

                        rows_needed = max(5, (img.height // 20) + 2)
                        current_row += rows_needed
                        total_screens += 1

                    except Exception as e:
                        print(f"Ошибка при вставке {filename}: {e}")
                        current_row += 10

            workbook.save(excel_path)
            print(f"Excel сохранён: {excel_path}")

            logger.excel_export(excel_path, total_screens)
            return excel_path, f"Экспортировано {total_screens} скриншотов в {len(subfolders)} лист(ов)"

        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            return None, f"Ошибка: {str(e)}"