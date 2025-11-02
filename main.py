import sys
from PyQt6.QtWidgets import QApplication, QDialog
from window import MainWindow
from PyQt6.QtGui import QIcon
from resource_path import resource_path
from database import db_manager

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    app.setStyle('Fusion')

    # Диалог выбора сервера
    from dialogs import ServerSelectionDialog
    server_dialog = ServerSelectionDialog()
    
    if server_dialog.exec() == QDialog.DialogCode.Accepted:
        selected_server = server_dialog.get_selected_server()
        
        # Сохраняем выбранный сервер в конфиг
        from config import config
        config.db_server = selected_server
        config.save_to_file()
        
        # Подключаемся к БД
        db_connected = db_manager.auto_connect()
        
        window = MainWindow()
        window.show()
        
        if db_connected:
            window.ui_manager.update_status(f"✅ Подключено к БД: {selected_server}", "color: green;")
        else:
            window.ui_manager.update_status(f"❌ Ошибка подключения к {selected_server}", "color: red;")
        
        sys.exit(app.exec())
    else:
        # Пользователь отменил выбор
        print("Выбор сервера отменен")
        sys.exit(1)


if __name__ == '__main__':
    main()