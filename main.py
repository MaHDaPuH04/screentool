import sys
from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
from PyQt6.QtGui import QIcon
from resource_path import resource_path
from config import config
from database import db_manager
from window import MainWindow
from logger import logger
from license_manager import license_manager
from datetime import datetime


def check_license_and_continue():
    """Проверяет лицензию и показывает диалог ввода при необходимости"""
    is_valid, message = license_manager.check_license()
    
    if is_valid:
        logger.info(f"✅ Лицензия проверена: {message}")
        return True
    
    # Требуем ввод ключа
    logger.warning(f"❌ Требуется лицензия: {message}")
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        # Показываем ТОЛЬКО формат ключа, а не реальный ключ!
        example_key = "XXXX-XXXX-XXXX-XXXX"
        
        key, ok = QInputDialog.getText(
            None,
            "Активация лицензии",
            f"⚠️ Это приложение не авторизовано для работы на данном компьютере.\n\n"
            f"IP адрес: {license_manager.get_local_ip()}\n"
            # f"📅 Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Введите лицензионный ключ:\n"
            f"(осталось попыток: {max_attempts - attempts})\n\n"
            f"Формат ключа: {example_key}",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if not key or not key.strip():
            QMessageBox.warning(
                None, 
                "Активация отменена", 
                "Без активации лицензии приложение не может работать."
            )
            return False
        
        is_valid, msg = license_manager.verify_license_key(key.strip())
        
        if is_valid:
            license_manager.save_license(key.strip())
            logger.info("✅ Лицензия активирована успешно")
            QMessageBox.information(
                None,
                "Активация успешна",
                f"✅ Лицензия активирована!\n\nПриложение будет запущено."
            )
            return True
        else:
            attempts += 1
            logger.warning(f"Неверный ключ ({attempts}/{max_attempts}): {msg}")
            
            QMessageBox.warning(
                None,
                "Неверный ключ",
                f"❌ {msg}\n\n"
                f"Попытка {attempts} из {max_attempts}"
            )
            
            if attempts >= max_attempts:
                break
    
    return False


def main():
    # СНАЧАЛА СОЗДАЕМ QApplication
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    app.setStyle('Fusion')
    
    # ПОТОМ ПРОВЕРЯЕМ ЛИЦЕНЗИЮ (БЕЗ ПЕРЕДАЧИ app)
    if not check_license_and_continue():
        sys.exit(1)
    
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