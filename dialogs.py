"""
Модуль диалогов для Auto Screenshot Tool
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
from logger import logger


class IPInputDialog(QDialog):
    """Диалог ввода IP адреса VM"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ввод IP адреса VM")
        self.setFixedSize(300, 150)
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        layout = QVBoxLayout(self)

        # Текст с объяснением
        info_label = QLabel("Введите последнюю часть IP адреса VM:")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Поле ввода
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Например: 128")
        self.ip_input.textChanged.connect(self.validate_ip)
        layout.addWidget(self.ip_input)

        # Метка для ошибок
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Изначально кнопка OK отключена
        button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def validate_ip(self, text):
        """Проверяет корректность введенного IP"""
        try:
            if text.strip() == "":
                self.error_label.setText("")
                return False

            ip_part = int(text)
            if 1 <= ip_part <= 255:
                self.error_label.setText("")
                # Включаем кнопку OK если IP корректен
                self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
                logger.debug(f"IP валиден: {ip_part}")
                return True
            else:
                self.error_label.setText("IP часть должна быть от 1 до 255")
                self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                return False
        except ValueError:
            self.error_label.setText("Введите число от 1 до 255")
            self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            return False

    def get_ip_part(self):
        """Возвращает введенную часть IP"""
        return self.ip_input.text().strip()


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






