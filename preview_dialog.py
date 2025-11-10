"""
Диалог для показа превью последнего скриншота
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, Q_ARG
from PyQt6.QtGui import QPixmap
from logger import logger
import os


class PreviewDialog(QDialog):
    """Диалог для показа превью последнего скриншота"""
    
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Превью скриншота")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        self.title_label = QLabel("Последний скриншот:")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Изображение
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #cccccc; background-color: #f0f0f0;")
        self.image_label.setMinimumSize(580, 320)
        self.image_label.setText("Изображение загружается...")
        layout.addWidget(self.image_label)
        
        # Кнопка закрытия
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
    def set_screenshot(self, image_path, screenshot_count):
        """Устанавливает скриншот для показа"""
        try:
            # Обновляем заголовок
            self.title_label.setText(f"Последний скриншот ({screenshot_count}): {os.path.basename(image_path)}")
            
            # Загружаем изображение
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Масштабируем изображение под размеры label с сохранением пропорций
                scaled_pixmap = pixmap.scaled(
                    560, 300, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                logger.debug(f"Превью установлено для: {image_path}")
            else:
                self.image_label.setText("Не удалось загрузить изображение")
                logger.error(f"Не удалось загрузить изображение: {image_path}")
                
        except Exception as e:
            self.image_label.setText(f"Ошибка загрузки: {str(e)}")
            logger.error(f"Ошибка установки превью: {e}")
    
    def showEvent(self, event):
        """При показе диалога позиционируем его в правом верхнем углу ЭКРАНА"""
        super().showEvent(event)
        self.position_in_screen_corner()
    
    def position_in_screen_corner(self):
        """Позиционирует диалог в правом верхнем углу экрана"""
        try:
            # Получаем геометрию основного экрана
            screen_geometry = self.screen().availableGeometry()
            
            # Вычисляем позицию в правом верхнем углу экрана
            x = screen_geometry.right() - self.width()   # 0px отступ от правого края
            y = screen_geometry.top()   # 0px отступ от верхнего края
            
            self.move(x, y)
            logger.debug(f"Превью позиционировано в правом верхнем углу экрана: ({x}, {y})")
            logger.debug(f"Размеры экрана: {screen_geometry.width()}x{screen_geometry.height()}")
                
        except Exception as e:
            logger.error(f"Ошибка позиционирования превью: {e}")
            # Fallback: центрируем на экране
            screen_geometry = self.screen().availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def closeEvent(self, event):
        """При закрытии испускаем сигнал"""
        self.closed.emit()
        super().closeEvent(event)