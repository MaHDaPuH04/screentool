"""
Модуль для управления файлами и папками
"""
import os
from logger import logger
import shutil


class FileManager:
    """Менеджер для работы с файлами"""
    
    @staticmethod
    def clear_screenshots_folder(screenshot_manager):
        """Очищает папку от group_ папок со скриншотами"""
        try:
            # Используем base_save_path (корневая папка)
            if not hasattr(screenshot_manager, 'base_save_path') or not screenshot_manager.base_save_path:
                return False, "Не выбрана папка для очистки"

            base_path = screenshot_manager.base_save_path
            
            if not os.path.exists(base_path):
                return False, "Папка не существует"

            # Находим все group_ папки
            group_folders = [
                f for f in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, f)) and f.startswith('group_')
            ]

            if not group_folders:
                return True, "Нет group_ папок для очистки"

            deleted_folders_count = 0

            # Удаляем каждую group_ папку
            for folder in group_folders:
                folder_path = os.path.join(base_path, folder)
                try:
                    # Рекурсивно удаляем папку со всем содержимым
                    shutil.rmtree(folder_path)
                    deleted_folders_count += 1
                    logger.info(f"Удалена папка: {folder}")
                    
                except Exception as e:
                    logger.error(f"Ошибка удаления папки {folder}: {e}")
                    return False, f"Ошибка удаления папки {folder}"

            # Сбрасываем состояние менеджера скриншотов
            screenshot_manager.screenshot_count = 0
            screenshot_manager.screenshot_taken.emit(0)
            
            # Сбрасываем группировку
            screenshot_manager.group_index = 1
            screenshot_manager.current_group = f"group_{screenshot_manager.group_index:03d}"
            # Создаем первую группу заново
            new_group_path = os.path.join(base_path, screenshot_manager.current_group)
            os.makedirs(new_group_path, exist_ok=True)
            screenshot_manager.save_path = new_group_path

            logger.info(f"Очистка завершена: удалено {deleted_folders_count} папок")
            
            return True, f"Удалено {deleted_folders_count} папок со скриншотами"

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






