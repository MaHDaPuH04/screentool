"""
Модуль для управления файлами и папками
"""
import os
from logger import logger
import shutil


class FileManager:
    @staticmethod
    def clear_screenshots_folder(screenshot_manager):
        """Очищает папку от всех групп скриншотов, созданных программой"""
        try:
            if not hasattr(screenshot_manager, 'base_save_path') or not screenshot_manager.base_save_path:
                return False, "Не выбрана папка для очистки"

            base_path = screenshot_manager.base_save_path
            
            if not os.path.exists(base_path):
                return False, "Папка не существует"

            # ТОЛЬКО ПАПКИ, КОТОРЫЕ МОГУТ БЫТЬ СОЗДАНЫ ПРОГРАММОЙ
            # 1. Предопределенные группы из screenshot_manager
            all_groups = screenshot_manager.predefined_groups.copy()
            
            # 2. Press группы (только те, что могли быть созданы)
            # Получаем текущий индекс из менеджера для определения максимального номера
            max_press_groups = 50  # Максимальное количество press групп
            for i in range(1, max_press_groups + 1):
                all_groups.append(f"press_{i}")
            
            deleted_folders_count = 0
            deleted_files_count = 0
            skipped_items = []

            # Проходим по всем элементам в базовой папке
            for item_name in os.listdir(base_path):
                item_path = os.path.join(base_path, item_name)
                
                # Пропускаем файлы (оставляем Excel файлы и другие)
                if os.path.isfile(item_path):
                    skipped_items.append(item_name)
                    continue
                
                # Удаляем ТОЛЬКО папки из нашего списка
                if item_name in all_groups and os.path.isdir(item_path):
                    try:
                        # Считаем количество файлов в папке перед удалением
                        files_in_folder = [f for f in os.listdir(item_path) 
                                        if os.path.isfile(os.path.join(item_path, f))]
                        deleted_files_count += len(files_in_folder)
                        
                        # Рекурсивно удаляем папку со всем содержимым
                        shutil.rmtree(item_path)
                        deleted_folders_count += 1
                        logger.info(f"Удалена папка: {item_name} (файлов: {len(files_in_folder)})")
                        
                    except Exception as e:
                        logger.error(f"Ошибка удаления папки {item_name}: {e}")
                        return False, f"Ошибка удаления папки {item_name}"
                else:
                    # Пропускаем другие папки (не созданные программой)
                    if os.path.isdir(item_path):
                        skipped_items.append(f"[папка] {item_name}")
                    else:
                        skipped_items.append(item_name)

            # Сбрасываем состояние менеджера скриншотов
            screenshot_manager.screenshot_count = 0
            screenshot_manager.screenshot_taken.emit(0)
            
            # Сбрасываем группировку
            screenshot_manager.group_index = 1
            screenshot_manager.press_index = 1
            screenshot_manager.current_group = screenshot_manager.predefined_groups[0]
            
            # Не создаем новую папку (будет создана по другому триггеру)
            screenshot_manager.save_path = None

            # Логируем пропущенные элементы
            if skipped_items:
                logger.info(f"Пропущенные элементы при очистке: {', '.join(skipped_items)}")

            logger.info(f"Очистка завершена: удалено {deleted_folders_count} папок, {deleted_files_count} файлов")
            
            return True, f"Удалено {deleted_folders_count} папок ({deleted_files_count} скриншотов)"

        except Exception as e:
            logger.error(f"Ошибка очистки папки: {str(e)}")
            return False, f"Ошибка очистки папки: {str(e)}"