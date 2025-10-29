from PyQt6.QtWidgets import QApplication
from window import MainWindow
from PyQt6.QtGui import QIcon
from resource_path import resource_path


def main():
    app = QApplication(sys.argv)
    
    # Пробуем несколько способов загрузки иконки
    icon_loaded = False
    
    # Способ 1: Через resource_path (для собранного exe)
    try:
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"Icon loaded from: {icon_path}")
            icon_loaded = True
    except Exception as e:
        print(f"Resource path method failed: {e}")
    
    # Способ 2: Прямой путь (для разработки)
    if not icon_loaded and os.path.exists('icon.ico'):
        app.setWindowIcon(QIcon('icon.ico'))
        print("Icon loaded from current directory")
        icon_loaded = True
    
    # Способ 3: Абсолютный путь
    if not icon_loaded:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, 'icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"Icon loaded from: {icon_path}")
            icon_loaded = True
    
    if not icon_loaded:
        print("WARNING: Icon file not found!")
    
    # Настройка стиля приложения
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()