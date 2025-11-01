import sys
from PyQt6.QtWidgets import QApplication
from window import MainWindow
from PyQt6.QtGui import QIcon
from resource_path import resource_path


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    # Настройка стиля приложения
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()