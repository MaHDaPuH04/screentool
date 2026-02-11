"""
Модуль диалогов для Auto Screenshot Tool
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QDialogButtonBox, QMessageBox, QComboBox, QPushButton)


class CleanupDialog:
    """Класс для показа диалогов очистки"""
    
    @staticmethod
    def show_cleanup_question(parent, message):
        """Показывает диалог вопроса об очистке скриншотов"""
        reply = QMessageBox.question(
            parent,
            "Очистка скриншотов",
            "Файл успешно отправлен на VM. Очистить папку от скриншотов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def show_success_message(parent, message, clear_message):
        """Показывает сообщение об успехе"""
        QMessageBox.information(parent, "Успех",
                               f"Файл отправлен на VM\n{clear_message}")
    
    @staticmethod
    def show_cleanup_error(parent, clear_message):
        """Показывает ошибку очистки"""
        QMessageBox.warning(parent, "Ошибка очистки", clear_message)




