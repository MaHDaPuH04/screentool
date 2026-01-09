"""
Диалог для показа превью последнего скриншота
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QKeyEvent, QResizeEvent
from logger import logger
import os
import glob


class PreviewDialog(QDialog):
    """Диалог для показа превью скриншотов с навигацией"""
    
    closed = pyqtSignal()
    screenshot_changed = pyqtSignal(str)  # Сигнал при смене скриншота
    
    def __init__(self, parent=None, screenshot_manager=None):
        super().__init__(parent)
        self.screenshot_manager = screenshot_manager
        self.current_screenshot_index = 0
        self.screenshots_list = []
        self.original_size = None  # Сохраняем оригинальный размер
        
        self.setWindowTitle("Превью скриншотов")
        # Устанавливаем фиксированный минимальный размер
        self.setMinimumSize(600, 350)
        # НЕ устанавливаем фиксированный размер, чтобы можно было максимизировать
        self.setBaseSize(600, 350)
        
        # Стандартные флаги окна с кнопками управления
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setup_ui()
        if screenshot_manager:
            self.load_all_screenshots()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ С ЗАГОЛОВКОМ И СЧЁТЧИКОМ ===
        header_layout = QHBoxLayout()
        
        # Заголовок
        self.title_label = QLabel("Превью скриншотов")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.title_label)
        
        # Счетчик скриншотов (в правом углу)
        self.counter_label = QLabel("0/0")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.counter_label.setStyleSheet("""
            color: #2A9D8F; 
            font-weight: bold; 
            font-size: 14px;
            padding: 4px 12px;
            border: 1px solid #2A9D8F;
            border-radius: 12px;
            background-color: #f8f9fa;
            margin-right: 10px;
        """)
        header_layout.addWidget(self.counter_label)
        
        header_layout.setStretchFactor(self.title_label, 3)
        header_layout.setStretchFactor(self.counter_label, 1)
        
        layout.addLayout(header_layout)
        
        # === ОБЛАСТЬ ИЗОБРАЖЕНИЯ ===
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            border: 2px solid #dee2e6; 
            background-color: #f8f9fa;
            border-radius: 8px;
            margin: 5px;
        """)
        # Устанавливаем минимальный размер для области изображения
        self.image_label.setMinimumSize(580, 300)
        layout.addWidget(self.image_label, 1)  # Растягиваем по вертикали
        
        # === ПОДСКАЗКА ДЛЯ ПОЛЬЗОВАТЕЛЯ ===
        hint_label = QLabel("← → стрелки для навигации | F11 - полноэкранный режим")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #6c757d; font-size: 9pt; font-style: italic; padding: 5px;")
        layout.addWidget(hint_label)
        
        # Устанавливаем фокус для захвата клавиатуры
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Сохраняем минимальный размер
        self.original_size = self.minimumSize()
    
    def set_screenshot_manager(self, manager):
        """Устанавливает менеджер скриншотов"""
        self.screenshot_manager = manager
        self.load_all_screenshots()
    
    def load_all_screenshots(self):
        """Загружает список всех скриншотов из текущей группы"""
        if not self.screenshot_manager:
            logger.warning("Менеджер скриншотов не установлен")
            return
            
        try:
            # Получаем путь к текущей группе
            if hasattr(self.screenshot_manager, 'get_current_group_path'):
                current_group_path = self.screenshot_manager.get_current_group_path()
            elif hasattr(self.screenshot_manager, 'save_path'):
                current_group_path = self.screenshot_manager.save_path
            else:
                logger.error("Не удалось получить путь к группе скриншотов")
                return
            
            if not os.path.exists(current_group_path):
                logger.warning(f"Путь не существует: {current_group_path}")
                return
            
            # Собираем все скриншоты в текущей группе
            self.screenshots_list = []
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                pattern = os.path.join(current_group_path, ext)
                files = glob.glob(pattern)
                # Фильтруем только скриншоты
                files = [f for f in files if os.path.basename(f).startswith('screenshot_')]
                self.screenshots_list.extend(files)
            
            # Сортируем по времени создания
            self.screenshots_list.sort(key=lambda x: os.path.getmtime(x))
            
            # Устанавливаем текущий индекс на последний скриншот
            if self.screenshots_list:
                self.current_screenshot_index = len(self.screenshots_list) - 1
                
            logger.debug(f"Загружено {len(self.screenshots_list)} скриншотов")
            self.update_counter_display()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки списка скриншотов: {e}")
    
    def set_screenshot(self, image_path, screenshot_count):
        """Устанавливает конкретный скриншот для показа"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"Файл не найден: {image_path}")
                return
            
            # Если список пустой, загружаем все скриншоты
            if not self.screenshots_list:
                self.load_all_screenshots()
            
            # Проверяем, есть ли этот файл в списке
            if image_path in self.screenshots_list:
                self.current_screenshot_index = self.screenshots_list.index(image_path)
            else:
                # Добавляем новый файл в список
                self.screenshots_list.append(image_path)
                self.screenshots_list.sort(key=lambda x: os.path.getmtime(x))
                self.current_screenshot_index = self.screenshots_list.index(image_path)
            
            self._display_screenshot(image_path)
            self.update_counter_display()
            
        except Exception as e:
            self.image_label.setText(f"Ошибка загрузки: {str(e)}")
            logger.error(f"Ошибка установки превью: {e}")
    
    def _display_screenshot(self, image_path):
        """Отображает скриншот с правильным масштабированием"""
        try:
            # Загружаем изображение
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.image_label.setText("Не удалось загрузить изображение")
                return
            
            # Получаем размер области для отображения
            label_size = self.image_label.size()
            available_width = max(label_size.width() - 20, 100)  # Минимум 100px
            available_height = max(label_size.height() - 20, 100)
            
            # Получаем оригинальные размеры
            original_width = pixmap.width()
            original_height = pixmap.height()
            
            # Рассчитываем масштабирование
            width_ratio = available_width / original_width
            height_ratio = available_height / original_height
            scale_ratio = min(width_ratio, height_ratio, 1.0)  # Не увеличиваем выше оригинала
            
            # Рассчитываем новые размеры
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # Масштабируем изображение
            scaled_pixmap = pixmap.scaled(
                new_width, 
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
            # Обновляем заголовок
            filename = os.path.basename(image_path)
            self.title_label.setText(f"Превью: {filename}")
            
            logger.debug(f"Превью установлено: {filename}, размер: {new_width}x{new_height}")
            
        except Exception as e:
            logger.error(f"Ошибка отображения скриншота: {e}")
    
    def update_counter_display(self):
        """Обновляет счетчик скриншотов"""
        if self.screenshots_list:
            total = len(self.screenshots_list)
            current = self.current_screenshot_index + 1
            self.counter_label.setText(f"{current}/{total}")
        else:
            self.counter_label.setText("0/0")
    
    def show_previous(self):
        """Показать предыдущий скриншот"""
        if self.current_screenshot_index > 0:
            self.current_screenshot_index -= 1
            image_path = self.screenshots_list[self.current_screenshot_index]
            self._display_screenshot(image_path)
            self.update_counter_display()
            self.screenshot_changed.emit(image_path)
    
    def show_next(self):
        """Показать следующий скриншот"""
        if self.current_screenshot_index < len(self.screenshots_list) - 1:
            self.current_screenshot_index += 1
            image_path = self.screenshots_list[self.current_screenshot_index]
            self._display_screenshot(image_path)
            self.update_counter_display()
            self.screenshot_changed.emit(image_path)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Обработка нажатий клавиш"""
        key = event.key()
        
        # Стрелка влево - предыдущий скриншот
        if key == Qt.Key.Key_Left:
            self.show_previous()
            
        # Стрелка вправо - следующий скриншот
        elif key == Qt.Key.Key_Right:
            self.show_next()
            
        # F11 - переключение полноэкранного режима
        elif key == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                # Восстанавливаем минимальный размер после выхода из полноэкранного режима
                self.resize(self.original_size)
            else:
                self.showFullScreen()
                
        # Escape - выход из полноэкранного режима
        elif key == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
            # Восстанавливаем минимальный размер
            self.resize(self.original_size)
            
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event: QResizeEvent):
        """При изменении размера окна перерисовываем изображение"""
        super().resizeEvent(event)
        
        # Перерисовываем текущее изображение при изменении размера
        if self.screenshots_list and self.current_screenshot_index < len(self.screenshots_list):
            # Небольшая задержка для стабилизации размера
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self._refresh_image)
    
    def _refresh_image(self):
        """Обновляет отображение текущего изображения"""
        if self.screenshots_list and self.current_screenshot_index < len(self.screenshots_list):
            current_image = self.screenshots_list[self.current_screenshot_index]
            self._display_screenshot(current_image)
    
    def showEvent(self, event):
        """При показе диалога позиционируем его в правом верхнем углу ЭКРАНА"""
        super().showEvent(event)
        
        # Устанавливаем минимальный размер при показе
        if not self.isFullScreen():
            self.resize(self.original_size)
            self.position_in_screen_corner()
    
    def position_in_screen_corner(self):
        """Позиционирует диалог в правом верхнем углу экрана"""
        try:
            screen_geometry = self.screen().availableGeometry()
            x = screen_geometry.right() - self.width()  # 0px отступ от края
            y = screen_geometry.top() # 0px отступ сверху
            self.move(x, y)
            logger.debug(f"Превью позиционировано: ({x}, {y})")
        except Exception as e:
            logger.error(f"Ошибка позиционирования превью: {e}")
            # Центрируем как запасной вариант
            screen_geometry = self.screen().availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
    
    def changeEvent(self, event):
        """Обработка изменения состояния окна (максимизация/восстановление)"""
        if event.type() == event.Type.WindowStateChange:
            # Если окно восстанавливается из максимизированного состояния
            if not self.isMaximized() and not self.isFullScreen():
                # Восстанавливаем минимальный размер
                self.resize(self.original_size)
                self.position_in_screen_corner()
        
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """При закрытии испускаем сигнал"""
        self.closed.emit()
        super().closeEvent(event)

    def remove_current_screenshot(self):
        """Удаляет текущий скриншот из списка и обновляет отображение"""
        if not self.screenshots_list or self.current_screenshot_index >= len(self.screenshots_list):
            return False
        
        try:
            # Удаляем файл с диска
            image_path = self.screenshots_list[self.current_screenshot_index]
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Удален файл: {image_path}")
            
            # Удаляем из списка
            removed_path = self.screenshots_list.pop(self.current_screenshot_index)
            
            # Если список пуст
            if not self.screenshots_list:
                self.current_screenshot_index = 0
                self.image_label.setText("Нет скриншотов")
                self.title_label.setText("Превью скриншотов")
                self.update_counter_display()
                return True
            
            # Корректируем индекс
            if self.current_screenshot_index >= len(self.screenshots_list):
                self.current_screenshot_index = len(self.screenshots_list) - 1
            
            # Показываем новый текущий скриншот
            if self.screenshots_list:
                new_image_path = self.screenshots_list[self.current_screenshot_index]
                self._display_screenshot(new_image_path)
                self.update_counter_display()
                self.screenshot_changed.emit(new_image_path)
            
            logger.debug(f"Скриншот удален, осталось: {len(self.screenshots_list)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления скриншота из превью: {e}")
            return False
    
    def update_screenshot_list(self):
        """Обновляет список скриншотов из текущей группы"""
        self.load_all_screenshots()
        
        # Если список не пуст, показываем последний скриншот
        if self.screenshots_list:
            self.current_screenshot_index = len(self.screenshots_list) - 1
            image_path = self.screenshots_list[self.current_screenshot_index]
            self._display_screenshot(image_path)
            self.update_counter_display()
        else:
            self.image_label.setText("Нет скриншотов")
            self.title_label.setText("Превью скриншотов")
            self.update_counter_display()
    
    def handle_screenshot_deleted(self, deleted_path):
        """Обрабатывает удаление скриншота извне"""
        try:
            # Удаляем из списка, если есть
            if deleted_path in self.screenshots_list:
                old_index = self.screenshots_list.index(deleted_path)
                self.screenshots_list.remove(deleted_path)
                
                # Корректируем текущий индекс
                if self.current_screenshot_index >= len(self.screenshots_list):
                    self.current_screenshot_index = max(0, len(self.screenshots_list) - 1)
                elif self.current_screenshot_index >= old_index and self.current_screenshot_index > 0:
                    self.current_screenshot_index -= 1
                
                # Обновляем отображение, если есть скриншоты
                if self.screenshots_list:
                    new_image_path = self.screenshots_list[self.current_screenshot_index]
                    self._display_screenshot(new_image_path)
                else:
                    self.image_label.setText("Нет скриншотов")
                    self.title_label.setText("Превью скриншотов")
                
                self.update_counter_display()
                logger.debug(f"Скриншот удален из превью: {os.path.basename(deleted_path)}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки удаления скриншота: {e}")