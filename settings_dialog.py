"""
Диалог настроек для Auto Screenshot Tool
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QComboBox, QCheckBox, QPushButton,
                             QGroupBox, QSlider, QLineEdit, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config import config
from logger import logger
from vm_manager import VMManager

class SettingsDialog(QDialog):
    """Диалог настроек приложения"""
    
    settings_changed = pyqtSignal()  # Сигнал об изменении настроек
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(400, 500)
        self.vm_manager = VMManager()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Настройки приложения")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Группа настроек скриншотов
        screenshot_group = QGroupBox("Настройки скриншотов")
        screenshot_layout = QFormLayout()
        
        # # Качество изображения
        # self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        # self.quality_slider.setRange(1, 100)
        # self.quality_slider.setValue(config.screenshot_quality)
        # self.quality_label = QLabel(f"{config.screenshot_quality}%")
        # self.quality_slider.valueChanged.connect(self.update_quality_label)
        # screenshot_layout.addRow("Качество:", self.quality_slider)
        # screenshot_layout.addRow("", self.quality_label)
        
        # Формат изображения
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG"])
        self.format_combo.setCurrentText(config.screenshot_format)
        screenshot_layout.addRow("Формат:", self.format_combo)
        
        # Минимальный интервал
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 9)
        self.interval_spin.setPrefix("0.")
        self.interval_spin.setValue(int(config.min_interval * 10))
        self.interval_spin.setSuffix(" сек")
        screenshot_layout.addRow("Интервал между скриншотами:", self.interval_spin)
        
        # Максимальное количество скриншотов
        self.max_screenshots_spin = QSpinBox()
        self.max_screenshots_spin.setRange(10, 10000)
        self.max_screenshots_spin.setValue(config.max_screenshots)
        screenshot_layout.addRow("Подумать что можно сюда перенести для удобства:", self.max_screenshots_spin)
        
        screenshot_group.setLayout(screenshot_layout)
        layout.addWidget(screenshot_group)
        
        # Группа настроек VM
        vm_group = QGroupBox("Настройки для отладки соединения")
        vm_layout = QFormLayout()
        
        # Базовый IP
        self.base_ip_edit = QLineEdit()
        self.base_ip_edit.setText(config.vm_base_ip)
        vm_layout.addRow("Базовый IP:", self.base_ip_edit)
        
        # Порты для сканирования
        self.ports_edit = QLineEdit()
        self.ports_edit.setText(", ".join(map(str, config.vm_scan_ports)))
        vm_layout.addRow("Порты для сканирования:", self.ports_edit)
        
        # Таймаут
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setValue(config.vm_timeout)
        self.timeout_spin.setSuffix(" сек")
        vm_layout.addRow("Таймаут:", self.timeout_spin)

        vm_group.setLayout(vm_layout)
        layout.addWidget(vm_group)
        
        # Группа настроек Excel
        excel_group = QGroupBox("Настройки Excel")
        excel_layout = QFormLayout()
        
        # Автооткрытие
        self.auto_open_check = QCheckBox()
        self.auto_open_check.setChecked(config.excel_auto_open)
        excel_layout.addRow("Автооткрытие:", self.auto_open_check)
        
        excel_group.setLayout(excel_layout)
        layout.addWidget(excel_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def update_quality_label(self, value):
        """Обновляет метку качества"""
        self.quality_label.setText(f"{value}%")
    
    def load_settings(self):
        """Загружает текущие настройки"""
        # Настройки уже загружены в setup_ui
        pass
    
    def save_settings(self):
        """Сохраняет настройки"""
        try:
            # Обновляем конфигурацию
            # config.screenshot_quality = self.quality_slider.value()
            config.screenshot_format = self.format_combo.currentText()
            config.min_interval = self.interval_spin.value() / 10.0
            config.max_screenshots = self.max_screenshots_spin.value()
            
            config.vm_base_ip = self.base_ip_edit.text()
            config.vm_timeout = self.timeout_spin.value()
            
            # Парсим порты
            try:
                ports_text = self.ports_edit.text()
                parsed_ports = [int(p.strip()) for p in ports_text.split(',') if p.strip().isdigit()]
                if parsed_ports:
                    config.vm_scan_ports = parsed_ports
                else:
                    logger.warning("Не найдено валидных портов, используем значения по умолчанию")
                    config.vm_scan_ports = [50000, 50001, 50002, 50003, 50004]
            except ValueError:
                logger.warning("Некорректные порты, используем значения по умолчанию")
                config.vm_scan_ports = [50000, 50001, 50002, 50003, 50004]
            
            config.excel_auto_open = self.auto_open_check.isChecked()
            
            # Сохраняем в файл
            config.save_to_file()
            
            logger.info("Настройки сохранены")
            self.settings_changed.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки: {str(e)}")
