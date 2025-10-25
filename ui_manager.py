"""
Модуль для управления пользовательским интерфейсом
"""
import os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from logger import logger


class UIManager:
    """Менеджер для управления UI состоянием"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.screenshot_manager = main_window.screenshot_manager
    
    def update_status(self, message, style=""):
        """Обновляет статус с возможным стилем"""
        self.main_window.status_label.setText(message)
        if style:
            self.main_window.status_label.setStyleSheet(style)
        logger.info(f"Статус обновлен: {message}")
    
    def update_counter(self, count):
        """Обновляет счетчик скриншотов"""
        self.main_window.counter_label.setText(f"Сделано скриншотов: {count}")
    
    def update_progress(self, value, visible):
        """Обновляет прогресс бар"""
        self.main_window.progress_bar.setValue(value)
        self.main_window.progress_bar.setVisible(visible)
    
    def show_capture_error(self):
        """Показывает сообщение об ошибке захвата"""
        QMessageBox.warning(
            self.main_window,
            "Ошибка захвата",
            "Функция захвата активного окна отъехала. Выключи и включи крыжечку"
        )
        # Автоматически выключаем переключатель
        self.main_window.capture_checkbox.setChecked(False)
        self.screenshot_manager.stop_capture()
        logger.warning("Показана ошибка захвата")
    
    def clear_status_style_after_delay(self, delay_ms=3000):
        """Убирает стиль статуса через указанное время"""
        QTimer.singleShot(delay_ms, lambda: self.main_window.status_label.setStyleSheet(""))
    
    def lock_ui_for_operation(self):
        """Блокирует UI для операции"""
        self.main_window.vm_btn.setEnabled(False)
        self.main_window.progress_bar.setVisible(True)
        logger.debug("UI заблокирован для операции")
    
    def unlock_ui_after_operation(self):
        """Разблокирует UI после операции"""
        self.main_window.vm_btn.setEnabled(True)
        self.main_window.progress_bar.setVisible(False)
        logger.debug("UI разблокирован после операции")
    
    def validate_save_path(self, path):
        """Проверяет доступность папки для записи"""
        try:
            test_file = os.path.join(path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception as e:
            logger.error(f"Папка недоступна для записи: {e}")
            return False
    
    def show_path_error(self, error_message):
        """Показывает ошибку с папкой"""
        QMessageBox.warning(
            self.main_window, 
            "Ошибка", 
            f"Папка недоступна для записи: {error_message}"
        )
    
    def show_folder_selection_error(self):
        """Показывает ошибку выбора папки"""
        QMessageBox.warning(
            self.main_window, 
            "Ошибка",
            "Не удалось установить папку для сохранения. Проверьте права доступа."
        )
    
    def reset_ui_after_folder_selection(self):
        """Сбрасывает UI после выбора папки"""
        self.main_window.capture_checkbox.setChecked(False)
        self.main_window.hotkey_checkbox.setChecked(False)
        self.screenshot_manager.stop_capture()
        self.screenshot_manager.disable_hotkey()
        logger.info("UI сброшен после выбора папки")






