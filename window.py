from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QCheckBox, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from resource_path import resource_path
from PyQt6.QtGui import QFont, QIcon
import shot
import os
from datetime import datetime
from excelexport import ExcelExporter
from logger import logger
from config import config
from settings_dialog import SettingsDialog
from dialogs import IPInputDialog, CleanupDialog
from vm_manager import VMManager
from ui_manager import UIManager
from file_manager import FileManager



class MainWindow(QMainWindow):
    # Добавляем кастомные сигналы для межпоточного общения
    update_status_signal = pyqtSignal(str)
    update_status_style_signal = pyqtSignal(str)
    unlock_ui_signal = pyqtSignal()
    show_cleanup_dialog_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.screenshot_manager = shot.ScreenshotManager()
        self.screenshot_manager.main_window = self
        self.excel_exporter = ExcelExporter()
        
        # Инициализируем менеджеры
        self.vm_manager = VMManager()
        self.ui_manager = UIManager(self)
        self.file_manager = FileManager()
        
        self.setWindowIcon(QIcon(resource_path('icon.ico')))
        self.setup_ui()
        self.connect_signals()

        # Подключаем новые сигналы
        self.update_status_signal.connect(self.status_label.setText)
        self.update_status_style_signal.connect(self.status_label.setStyleSheet)
        self.unlock_ui_signal.connect(self._unlock_ui)
        self.show_cleanup_dialog_signal.connect(self._show_cleanup_dialog)

    def _unlock_ui(self):
        """Разблокировка UI (вызывается через сигнал)"""
        self.ui_manager.unlock_ui_after_operation()

    def show_ip_input_dialog(self):
        from PyQt6.QtWidgets import QDialog
        """Показывает диалог ввода IP и возвращает результат"""
        dialog = IPInputDialog(self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            ip_part = dialog.get_ip_part()
            if ip_part:
                try:
                    self.vm_manager.set_ip_part(ip_part)
                    self.ui_manager.update_status(f"IP установлен: 10.7.128.{ip_part}", "color: green;")
                    return True
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Неверный IP: {str(e)}")
                    return False
        return False

    def send_to_vm(self):
        """Отправляет Excel на VM с проверкой IP и последующей очисткой скриншотов"""
        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return

        latest_excel = self.vm_manager.find_latest_excel_file(self.screenshot_manager.save_path)
        if not latest_excel:
            QMessageBox.warning(self, "Ошибка", "Не найден Excel файл для отправки!")
            return

        # Проверяем, задан ли IP
        if self.vm_manager.manual_ip_part is None:
            if not self.show_ip_input_dialog():
                self.ui_manager.update_status("IP не задан - отправка отменена", "color: orange;")
                return

        # Блокируем UI
        self.ui_manager.lock_ui_for_operation()
        self.ui_manager.update_status(f"Отправка {os.path.basename(latest_excel)} на VM...")

        def send_thread():
            try:
                # Получаем путь к VM с автоматическим определением порта
                vm_path = self.vm_manager._get_vm_path()
                if not vm_path:
                    self.update_status_signal.emit("❌ Не удалось определить путь к VM")
                    self.update_status_style_signal.emit("color: red;")
                    self.unlock_ui_signal.emit()
                    return

                # Копируем файл на VM
                success, message = self.vm_manager.copy_file_to_vm(latest_excel, vm_path)

                if success:
                    self.update_status_signal.emit(f"✅ {message}")
                    self.update_status_style_signal.emit("color: green;")
                    self.show_cleanup_dialog_signal.emit(message, latest_excel)
                else:
                    self.update_status_signal.emit(f"❌ {message}")
                    self.update_status_style_signal.emit("color: red;")
                    self.unlock_ui_signal.emit()

            except Exception as e:
                error_msg = f"💥 Ошибка копирования: {str(e)}"
                self.update_status_signal.emit(error_msg)
                self.update_status_style_signal.emit("color: red;")
                self.unlock_ui_signal.emit()

        # Запускаем в отдельном потоке
        import threading
        thread = threading.Thread(target=send_thread, daemon=True)
        thread.start()

    def _show_cleanup_dialog(self, message, excel_file):
        """Показывает диалог очистки (вызывается через сигнал в основном потоке)"""
        if CleanupDialog.show_cleanup_question(self, message):
            self.ui_manager.update_status("Очистка скриншотов...")

            # Очищаем скриншоты
            clear_success, clear_message = self.file_manager.clear_screenshots_folder(self.screenshot_manager)

            if clear_success:
                self.ui_manager.update_status(f"✅ {message} + {clear_message}", "color: green;")
                CleanupDialog.show_success_message(self, message, clear_message)
            else:
                self.ui_manager.update_status(f"✅ {message} (Ошибка очистки: {clear_message})", "color: orange;")
                CleanupDialog.show_cleanup_error(self, clear_message)
        else:
            self.ui_manager.update_status(f"✅ {message} (скриншоты сохранены)", "color: green;")

        # Всегда разблокируем UI после диалога
        self.ui_manager.unlock_ui_after_operation()

    #Методы управления окном
    def minimize_window(self):
        """Сворачивает окно приложения"""
        self.showMinimized()
        logger.debug("Окно приложения свернуто")
    
    def restore_window(self):
        """Восстанавливает окно приложения"""
        self.showNormal()
        self.activateWindow()  # Активируем окно
        self.raise_()  # Поднимаем на передний план
        logger.debug("Окно приложения восстановлено")

    def setup_ui(self):
        self.setWindowTitle("Auto Screenshot Tool v 1.0.4")
        self.setFixedSize(500, 460)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel("Auto Screenshot Tool")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Группа настроек
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout()

        # Переключатели
        self.delete_last_checkbox = QCheckBox("Delete для удаления последнего скриншота")
        self.capture_checkbox = QCheckBox("Включить захват активного окна")
        self.hotkey_checkbox = QCheckBox("Включить горячую клавишу Insert(Print Screen)")

        settings_layout.addWidget(self.delete_last_checkbox)
        settings_layout.addWidget(self.capture_checkbox)
        settings_layout.addWidget(self.hotkey_checkbox)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Информация о папке
        self.folder_label = QLabel("Папка сохранения: не выбрана")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        # Кнопка выбора папки
        self.select_folder_btn = QPushButton("Выбрать папку для сохранения")
        self.select_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.select_folder_btn.setToolTip("Скриншотов и Excel-файла")
        layout.addWidget(self.select_folder_btn)

        # Счетчик скриншотов
        self.counter_label = QLabel("Сделано скриншотов: 0")
        layout.addWidget(self.counter_label)

        # ГРУППА ДЛЯ ЧЕТЫРЕХ КНОПОК
        buttons_group = QGroupBox("Действия")
        buttons_layout = QHBoxLayout()  # Горизонтальный layout для кнопок

        # Кнопка "Настроить IP"
        self.ip_btn = QPushButton("№ VSAT'а")
        self.ip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #696969;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #C0C0C0;
                }
            """)
        self.ip_btn.setToolTip("Можешь вписать, но пока не функциональна")

        # Кнопка "Экспорт в Excel"
        self.excel_btn = QPushButton("Экспорт в Excel")
        self.excel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #696969;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #C0C0C0;
                }
                QPushButton:disabled {
                    background-color: #C0C0C0;
                    color: #757575;
                }
            """)
        self.excel_btn.setToolTip("Экспорт скриншотов в Excel")

        # Кнопка "Очистить Папку"
        self.vm_btn = QPushButton("Очистить Папку")
        self.vm_btn.setStyleSheet("""
                QPushButton {
                    background-color: #696969;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #C0C0C0;
                }
                QPushButton:disabled {
                    background-color: #C0C0C0;
                    color: #757575;
                }
            """)
        self.vm_btn.setToolTip("Очистить папку от скриншотов (Excel файлы сохраняются)")

        # Кнопка "Настройки"
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        self.settings_btn.setToolTip("Настройки приложения")
        self.settings_btn.setFixedWidth(50)

        # Добавляем кнопки в горизонтальный layout
        buttons_layout.addWidget(self.ip_btn)
        buttons_layout.addWidget(self.excel_btn)
        buttons_layout.addWidget(self.vm_btn)
        buttons_layout.addWidget(self.settings_btn)

        # Устанавливаем растяжение
        buttons_layout.setStretchFactor(self.ip_btn, 1)
        buttons_layout.setStretchFactor(self.excel_btn, 1)
        buttons_layout.setStretchFactor(self.vm_btn, 1)

        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()

        self.send_btn = QPushButton("Отправить")
        self.send_btn.clicked.connect(self.send_excel_to_vm)
        self.send_btn.setStyleSheet("""
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

        button_layout.addWidget(self.send_btn)
        layout.addLayout(button_layout)

    def send_excel_to_vm(self):
        """Отправляет Excel файл на VM используя VMManager"""
        try:
            if not self.screenshot_manager.save_path:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
                return

            # Ищем самый новый Excel файл через VMManager
            excel_file = self.vm_manager.find_latest_excel_file(self.screenshot_manager.save_path)
            
            if not excel_file:
                QMessageBox.warning(self, "Ошибка", "Не найден Excel файл для отправки!")
                return

            # Проверяем, задан ли IP
            if self.vm_manager.manual_ip_part is None:
                if not self.show_ip_input_dialog():
                    self.ui_manager.update_status("IP не задан - отправка отменена", "color: orange;")
                    return

            # Блокируем UI
            self.send_btn.setEnabled(False)
            self.ui_manager.update_status(f"Отправка {os.path.basename(excel_file)} на VM...", "color: blue;")

            # Отправляем файл используя метод из VMManager
            success, message = self.vm_manager.send_excel_to_vm(excel_file)

            # Показываем результат
            if success:
                self.ui_manager.update_status(f"✅ {message}", "color: green;")
                QMessageBox.information(self, "Успех", message)
                logger.info(f"Excel файл успешно отправлен: {excel_file}")
            else:
                self.ui_manager.update_status(f"❌ {message}", "color: red;")
                QMessageBox.warning(self, "Ошибка", message)
                logger.error(f"Ошибка отправки Excel файла: {message}")

        except Exception as e:
            error_msg = f"Ошибка при отправке файла: {str(e)}"
            self.ui_manager.update_status(f"💥 {error_msg}", "color: red;")
            QMessageBox.critical(self, "Ошибка", error_msg)
            logger.error(error_msg)
        finally:
            # Разблокируем кнопку
            self.send_btn.setEnabled(True)

    def connect_signals(self):
        self.capture_checkbox.stateChanged.connect(self.toggle_capture)
        self.hotkey_checkbox.stateChanged.connect(self.toggle_hotkey)
        self.delete_last_checkbox.stateChanged.connect(self.toggle_delete_last)
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.excel_btn.clicked.connect(self.export_to_excel)
        # self.vm_btn.clicked.connect(self.send_to_vm)
        self.vm_btn.clicked.connect(self.clear_screenshots_folder) #Временно заменено на очистку папки
        self.ip_btn.clicked.connect(self.show_ip_input_dialog)
        self.settings_btn.clicked.connect(self.show_settings)

        # Сигналы от менеджера скриншотов
        self.screenshot_manager.screenshot_taken.connect(self.update_counter)
        self.screenshot_manager.status_changed.connect(self.update_status)
        self.screenshot_manager.progress_changed.connect(self.update_progress)
        self.screenshot_manager.capture_error_detected.connect(self.show_capture_error)

    def toggle_capture(self, state):
        if state == Qt.CheckState.Checked.value:
            if not self.screenshot_manager.save_path:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
                self.capture_checkbox.setChecked(False)
                return

            # Проверка доступности папки
            if not self.ui_manager.validate_save_path(self.screenshot_manager.save_path):
                self.ui_manager.show_path_error("Папка недоступна для записи")
                self.capture_checkbox.setChecked(False)
                return

            self.screenshot_manager.start_capture()
        else:
            self.screenshot_manager.stop_capture()

    def toggle_hotkey(self, state):
        if state == Qt.CheckState.Checked.value:
            if not self.screenshot_manager.save_path:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
                self.hotkey_checkbox.setChecked(False)
                return

            # Проверка доступности папки
            if not self.ui_manager.validate_save_path(self.screenshot_manager.save_path):
                self.ui_manager.show_path_error("Папка недоступна для записи")
                self.hotkey_checkbox.setChecked(False)
                return

            self.screenshot_manager.enable_hotkey()
        else:
            self.screenshot_manager.disable_hotkey()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder:
            success = self.screenshot_manager.set_save_path(folder)
            if success:
                self.folder_label.setText(f"Папка сохранения: {folder}")
                # Сбрасываем UI после выбора папки
                self.ui_manager.reset_ui_after_folder_selection()
            else:
                self.ui_manager.show_folder_selection_error()

    def show_capture_error(self):
        """Показывает сообщение об ошибке захвата"""
        self.ui_manager.show_capture_error()
    
    def clear_screenshots_folder(self):
        """Очищает папку от скриншотов"""
        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return
        
        clear_success, clear_message = self.file_manager.clear_screenshots_folder(self.screenshot_manager)
        
        if clear_success:
            self.ui_manager.update_status(f"✅ {clear_message}", "color: green;")
            QMessageBox.information(self, "Успех", clear_message)
        else:
            self.ui_manager.update_status(f"❌ {clear_message}", "color: red;")
            QMessageBox.warning(self, "Ошибка", clear_message)

    def toggle_delete_last(self, state):
        """Включает/выключает режим удаления последнего скриншота по Delete"""
        if state == Qt.CheckState.Checked.value:
            self.ui_manager.update_status("Режим 'Delete для удаления' включен", "color: blue;")
            logger.info("Включен режим удаления последнего скриншота по Delete")
        else:
            self.ui_manager.update_status("Режим 'Delete для удаления' выключен", "color: gray;")
            logger.info("Выключен режим удаления последнего скриншота по Delete")

    def export_to_excel(self):
        """Экспорт скриншотов в Excel с диагностикой"""
        print("=== НАЖАТА КНОПКА ЭКСПОРТА ===")

        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return

        default_excel = os.path.join(
            self.screenshot_manager.save_path,
            f"screenshots_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        print(f"Предлагаемый путь: {default_excel}")

        excel_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить Excel файл",
            default_excel,
            "Excel Files (*.xlsx)"
        )

        if not excel_path:
            print("Пользователь отменил выбор файла")
            return

        print(f"Выбранный путь: {excel_path}")

        # Блокируем интерфейс
        self.excel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Экспорт в Excel...")

        # Принудительно обновляем интерфейс
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            print("Запускаем экспорт...")
            # Запускаем экспорт
            result_path, message = self.excel_exporter.export_screenshots_to_excel(
                self.screenshot_manager.save_path,
                excel_path
            )

            print(f"Результат: {result_path}")
            print(f"Сообщение: {message}")

            if result_path:
                self.status_label.setText(f"Успешно: {os.path.basename(result_path)}")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                # Показываем краткое сообщение
                QMessageBox.information(self, "Успех", f"Создан файл:\n{os.path.basename(result_path)}")
            else:
                self.status_label.setText(f"Ошибка: {message}")
                self.status_label.setStyleSheet("color: red;")
                QMessageBox.warning(self, "Ошибка", message)

        except Exception as e:
            error_msg = f"Исключение: {str(e)}"
            print(f"ИСКЛЮЧЕНИЕ: {e}")
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Ошибка", error_msg)

        finally:
            self.progress_bar.setVisible(False)
            self.excel_btn.setEnabled(True)

            # Убираем цвет через 3 секунды
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.status_label.setStyleSheet(""))

    def update_counter(self, count):
        self.ui_manager.update_counter(count)

    def update_status(self, message):
        self.ui_manager.update_status(message)

    def update_progress(self, value, visible):
        self.ui_manager.update_progress(value, visible)

    def show_settings(self):
        """Показывает диалог настроек"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()
    
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        logger.info("Настройки изменены, обновляем конфигурацию")
        # Перезагружаем конфигурацию
        config.load_from_file()
        
        # Обновляем настройки менеджера скриншотов
        self.screenshot_manager.min_interval = config.min_interval
        self.screenshot_manager.max_screenshots = config.max_screenshots
        
        self.ui_manager.update_status("Настройки обновлены", "color: green;")
        self.ui_manager.clear_status_style_after_delay()

    def closeEvent(self, event):
        self.screenshot_manager.cleanup()
        event.accept()

    
    