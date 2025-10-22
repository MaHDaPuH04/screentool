"""
Модуль для управления файлами и папками
"""
import os
from logger import logger


class FileManager:
    """Менеджер для работы с файлами"""
    
    @staticmethod
    def clear_screenshots_folder(screenshot_manager):
        """Очищает папку от скриншотов, сохраняя Excel файлы"""
        try:
            if not screenshot_manager.save_path:
                return False, "Не выбрана папка для очистки"

            screenshot_files = []
            excel_files = []

            # Собираем все файлы в папке
            for filename in os.listdir(screenshot_manager.save_path):
                file_path = os.path.join(screenshot_manager.save_path, filename)
                if filename.lower().endswith('.png') and filename.startswith('screenshot_'):
                    screenshot_files.append(file_path)
                elif filename.lower().endswith('.xlsx'):
                    excel_files.append(file_path)

            # Удаляем только скриншоты
            deleted_count = 0
            for screenshot_file in screenshot_files:
                try:
                    os.remove(screenshot_file)
                    deleted_count += 1
                    logger.debug(f"Удален: {os.path.basename(screenshot_file)}")
                except Exception as e:
                    logger.error(f"Ошибка удаления {screenshot_file}: {e}")

            # Сбрасываем счетчик скриншотов
            screenshot_manager.screenshot_count = 0
            screenshot_manager.screenshot_taken.emit(0)

            logger.info(f"Очистка завершена: удалено {deleted_count} скриншотов, сохранено {len(excel_files)} Excel файлов")
            return True, f"Удалено {deleted_count} скриншотов. Сохранено {len(excel_files)} Excel файлов."

        except Exception as e:
            logger.error(f"Ошибка очистки папки: {str(e)}")
            return False, f"Ошибка очистки папки: {str(e)}"
    
    @staticmethod
    def get_screenshot_files(save_path):
        """Получает список файлов скриншотов"""
        try:
            screenshot_files = []
            for filename in os.listdir(save_path):
                if filename.lower().endswith('.png') and filename.startswith('screenshot_'):
                    file_path = os.path.join(save_path, filename)
                    screenshot_files.append(file_path)
            return screenshot_files
        except Exception as e:
            logger.error(f"Ошибка получения списка скриншотов: {e}")
            return []
    
    @staticmethod
    def get_excel_files(save_path):
        """Получает список Excel файлов"""
        try:
            excel_files = []
            for filename in os.listdir(save_path):
                if filename.lower().endswith('.xlsx'):
                    file_path = os.path.join(save_path, filename)
                    excel_files.append(file_path)
            return excel_files
        except Exception as e:
            logger.error(f"Ошибка получения списка Excel файлов: {e}")
            return []
    
    @staticmethod
    def validate_file_path(file_path):
        """Проверяет существование файла"""
        if not os.path.exists(file_path):
            logger.warning(f"Файл не найден: {file_path}")
            return False
        return True
