import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from config import config
from logger import logger


class ExcelExporter:
    def export_screenshots_to_excel(self, screenshots_folder, excel_path=None):
        """
        Минимальная версия экспорта в Excel
        """
        print("=== НАЧАЛО ЭКСПОРТА ===")

        try:
            # Получаем список скриншотов
            screenshot_files = []
            for filename in os.listdir(screenshots_folder):
                if filename.lower().endswith('.png') and filename.startswith('screenshot_'):
                    file_path = os.path.join(screenshots_folder, filename)
                    created_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    screenshot_files.append((file_path, {
                        'filename': filename,
                        'created_time': created_time
                    }))

            print(f"Найдено файлов: {len(screenshot_files)}")

            if not screenshot_files:
                return None, "Нет скриншотов для экспорта"

            # Сортируем по дате создания
            screenshot_files.sort(key=lambda x: x[1]['created_time'])

            # Создаем путь для Excel файла
            if not excel_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                excel_path = os.path.join(screenshots_folder, f"PreRun_{timestamp}.xlsx")
            elif not excel_path.lower().endswith('.xlsx'):
                excel_path += '.xlsx'

            print(f"Путь для Excel: {excel_path}")

            # Создаем книгу Excel
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Скриншоты"

            # Настраиваем колонки
            worksheet.column_dimensions['A'].width = 10
            worksheet.column_dimensions['B'].width = 10
            worksheet.column_dimensions['C'].width = 10

            # Заголовки
            worksheet.cell(row=1, column=1, value="")
            worksheet.cell(row=1, column=2, value="")
            worksheet.cell(row=1, column=3, value="")

            current_row = 2

            for i, (file_path, file_info) in enumerate(screenshot_files, 1):
                print(f"Обрабатываю файл {i}: {file_info['filename']}")

                try:
                    # Пробуем вставить изображение
                    img = ExcelImage(file_path)
                    logger.debug(f"Размер изображения: {img.width}x{img.height}")

                    # Вставляем в колонку A с фактическим размером
                    img.anchor = f'A{current_row}'
                    worksheet.add_image(img)
                    logger.debug("Изображение добавлено в Excel")

                    # Добавляем информацию
                    worksheet.cell(row=current_row, column=2, value=file_info['filename'])
                    worksheet.cell(row=current_row, column=3,
                                   value=file_info['created_time'].strftime('%Y-%m-%d %H:%M:%S'))

                    # Переходим к следующей строке
                    rows_needed = max(5, (img.height // 20) + 2)
                    current_row += rows_needed
                    print(f"Переход к строке {current_row}")

                except Exception as e:
                    print(f"Ошибка при обработке файла {file_info['filename']}: {e}")
                    current_row += 10
                    continue

            print("Сохраняю Excel файл...")
            # Сохраняем файл
            workbook.save(excel_path)
            print("Файл успешно сохранен!")

            # Проверяем что файл создался
            if os.path.exists(excel_path):
                file_size = os.path.getsize(excel_path)
                print(f"Файл создан, размер: {file_size} байт")

                # Автооткрытие Excel файла
                if config.excel_auto_open:
                    try:
                        os.startfile(excel_path)
                        logger.info("Excel файл открыт для просмотра")
                    except Exception as e:
                        logger.warning(f"Не удалось открыть файл: {e}")

                logger.excel_export(excel_path, len(screenshot_files))
                return excel_path, f"Успешно экспортировано {len(screenshot_files)} скриншотов"
            else:
                print("Файл не создан!")
                return None, "Не удалось создать Excel файл"

        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            return None, f"Ошибка экспорта в Excel: {str(e)}"