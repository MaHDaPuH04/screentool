"""
Модуль для управления файлами и папками
"""
import os
from logger import logger
import shutil


class FileManager:
    @staticmethod
    def clear_screenshots_folder(screenshot_manager):
        """Очищает папку от всех групп скриншотов"""
        try:
            if not hasattr(screenshot_manager, 'base_save_path') or not screenshot_manager.base_save_path:
                return False, "Не выбрана папка для очистки"

            base_path = screenshot_manager.base_save_path
            
            if not os.path.exists(base_path):
                return False, "Папка не существует"

            # Получаем список всех возможных групп
            all_groups = []
            
            # Предопределенные группы
            predefined = ["poll+calib", "TIP", "ver", "TM", "PDT"]
            all_groups.extend(predefined)
            
            # Press группы (до 20 для проверки)
            for i in range(1, 21):
                all_groups.append(f"press_{i}")
            
            deleted_folders_count = 0

            # Удаляем каждую существующую группу
            for folder_name in all_groups:
                folder_path = os.path.join(base_path, folder_name)
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    try:
                        # Рекурсивно удаляем папку со всем содержимым
                        shutil.rmtree(folder_path)
                        deleted_folders_count += 1
                        logger.info(f"Удалена папка: {folder_name}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка удаления папки {folder_name}: {e}")
                        return False, f"Ошибка удаления папки {folder_name}"

            # Сбрасываем состояние менеджера скриншотов
            screenshot_manager.screenshot_count = 0
            screenshot_manager.screenshot_taken.emit(0)
            
            # Сбрасываем группировку
            screenshot_manager.group_index = 1
            screenshot_manager.press_index = 1
            screenshot_manager.current_group = screenshot_manager.predefined_groups[0]
            
            # Создаем первую группу заново
            new_group_path = os.path.join(base_path, screenshot_manager.current_group)
            os.makedirs(new_group_path, exist_ok=True)
            screenshot_manager.save_path = new_group_path

            logger.info(f"Очистка завершена: удалено {deleted_folders_count} папок")
            
            return True, f"Удалено {deleted_folders_count} папок со скриншотами"

        except Exception as e:
            logger.error(f"Ошибка очистки папки: {str(e)}")
            return False, f"Ошибка очистки папки: {str(e)}"