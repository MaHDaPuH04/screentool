import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from resource_path import resource_path
from config import config
from database import db_manager
from window import MainWindow
from logger import logger

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    app.setStyle('Fusion')

    logger.info("🚀 Запуск программы, автоматический выбор сервера БД...")

    best_server, success = db_manager.select_best_server()

    if success:
        db_connected = db_manager.auto_connect(best_server)
        if not db_connected:
            reply = QMessageBox.question(
                None,
                "Ошибка подключения",
                f"Не удалось подключиться к серверу {best_server}.\n"
                "Хотите продолжить в офлайн-режиме?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                sys.exit(1)
    else:
        reply = QMessageBox.question(
            None,
            "Нет доступа к БД",
            "Не удалось подключиться ни к одному серверу.\n"
            "Продолжить в офлайн-режиме?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            sys.exit(1)

    window = MainWindow()
    window.show()

    if db_manager.is_connected:
        window.ui_manager.update_status(f"✅ Подключено к БД: {config.db_server}", "color: green;")
    else:
        window.ui_manager.update_status("⚠️ Офлайн-режим (тестовые данные)", "color: orange;")

    sys.exit(app.exec())

if __name__ == '__main__':
    main()