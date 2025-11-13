"""
Модуль диалогов для Auto Screenshot Tool
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QDialogButtonBox, QMessageBox, QComboBox, QPushButton)
import pyodbc


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


class ServerSelectionDialog(QDialog):
    """Диалог выбора SQL Server"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор SQL Server")
        self.setFixedSize(400, 200)
        self.selected_server = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Текст с объяснением
        info_label = QLabel("Выберите DB полевой компьютер")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Выпадающий список серверов
        self.server_combo = QComboBox()
        self.server_combo.addItem("ADVMWD1\\ADVANTAGE2017", "ADVMWD1\\ADVANTAGE2017")
        self.server_combo.addItem("ADVMWD2\\ADVANTAGE2017", "ADVMWD2\\ADVANTAGE2017")
        # self.server_combo.addItem("TyuMWD212\\ADVANTAGE2017", "TyuMWD212\\ADVANTAGE2017")
        layout.addWidget(self.server_combo)

        # Кнопка тестирования подключения
        self.test_btn = QPushButton("Проверить подключение")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)

        # Метка для статуса
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                    QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def test_connection(self):
        """Проверяет подключение к выбранному серверу"""
        server = self.server_combo.currentData()
        try:
            conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={server};"
                f"DATABASE=advantage;"
                f"Trusted_Connection=yes;"
                f"Timeout=3;"
            )
            conn = pyodbc.connect(conn_str)
            conn.close()
            self.status_label.setText("✅ Подключение успешно!")
            self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

    def get_selected_server(self):
        """Возвращает выбранный сервер"""
        return self.server_combo.currentData()



