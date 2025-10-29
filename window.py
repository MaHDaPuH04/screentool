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
from dialogs import IPInputDialog, CleanupDialog
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
        self.next_sheet_requested = False
        
        # Инициализируем менеджеры
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
        self.setWindowTitle("Auto Screenshot Tool v 1.0.5")
        self.setFixedSize(500, 465)

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

       
        # Переключатели (группа настроек)
        self.delete_last_checkbox = QCheckBox("Delete для удаления последнего скриншота")
        self.capture_checkbox = QCheckBox("Включить захват активного окна")
        self.hotkey_checkbox = QCheckBox("Включить горячую клавишу Insert (Print Screen)")
        self.auto_open_check = QCheckBox("Автооткрывать Excel после экспорта")
        self.auto_open_check.setChecked(config.excel_auto_open)
                       

        settings_layout.addWidget(self.delete_last_checkbox)
        settings_layout.addWidget(self.capture_checkbox)
        settings_layout.addWidget(self.hotkey_checkbox)
        settings_layout.addWidget(self.auto_open_check)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group) 

        # Информация о папке
        self.folder_label = QLabel("Папка сохранения: не выбрана")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        # === ГРУППА ДЛЯ ВЫБОРА ПАПКИ И КНОПКИ "СЛЕДУЮЩИЙ ЛИСТ" ===
        folder_group = QGroupBox("Папка сохранения и лист Excel")
        folder_layout = QHBoxLayout()

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
        self.select_folder_btn.setToolTip("Выбрать папку для скриншотов и Excel-файлов")

        # Кнопка "Следующий лист"
        self.next_sheet_btn = QPushButton("Следующий лист")
        self.next_sheet_btn.setStyleSheet("""
            QPushButton {
                background-color: #808080;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #A9A9A9;
            }
        """)
        self.next_sheet_btn.setToolTip("Следующие скриншоты будут добавлены на новый лист Excel")

        folder_layout.addWidget(self.select_folder_btn)
        folder_layout.addWidget(self.next_sheet_btn)

        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Счетчик скриншотов
        self.counter_label = QLabel("Сделано скриншотов: 0")
        layout.addWidget(self.counter_label)

        # ГРУППА ДЛЯ двух КНОПОК
        buttons_group = QGroupBox("Действия")
        buttons_layout = QHBoxLayout()  # Горизонтальный layout для кнопок

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
                                         
        # Добавляем кнопки в горизонтальный layout
        buttons_layout.addWidget(self.excel_btn)
        buttons_layout.addWidget(self.vm_btn)
    

        # Устанавливаем растяжение
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

    def connect_signals(self):
        self.capture_checkbox.stateChanged.connect(self.toggle_capture)
        self.hotkey_checkbox.stateChanged.connect(self.toggle_hotkey)
        self.delete_last_checkbox.stateChanged.connect(self.toggle_delete_last)
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.excel_btn.clicked.connect(self.export_to_excel)
        self.vm_btn.clicked.connect(self.clear_screenshots_folder) #Временно заменено на очистку папки
        self.auto_open_check.stateChanged.connect(self.toggle_auto_open)
        self.next_sheet_btn.clicked.connect(self.request_next_sheet)

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
        print("=== НАЧАТА КНОПКА ЭКСПОРТА ===")

        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return

        # Используем base_save_path вместо save_path для поиска всех групп
        export_folder = self.screenshot_manager.base_save_path if hasattr(self.screenshot_manager, 'base_save_path') else self.screenshot_manager.save_path
    
        print(f"Экспортируем из папки: {export_folder}")
    
        # Проверим что в папке есть подпапки
        if export_folder and os.path.exists(export_folder):
            subfolders = [f for f in os.listdir(export_folder) if os.path.isdir(os.path.join(export_folder, f))]
            print(f"Найдено подпапок в {export_folder}: {len(subfolders)}")
            print(f"Подпапки: {subfolders}")

        default_excel = os.path.join(
            export_folder,
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
            # Запускаем экспорт из КОРНЕВОЙ папки (где лежат group_ папки)
            result_path, message = self.excel_exporter.export_screenshots_to_excel(
                export_folder,  # Используем корневую папку, а не текущую группу
                excel_path
            )

            print(f"Результат: {result_path}")
            print(f"Сообщение: {message}")

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

        if result_path:
            self.status_label.setText(f"Успешно: {os.path.basename(result_path)}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Успех", f"Создан файл:\n{os.path.basename(result_path)}")
    
            # Автоматическое открытие Excel, если включено
            if config.excel_auto_open:
                try:
                    os.startfile(result_path)
                except Exception as e:
                    logger.warning(f"Не удалось открыть Excel автоматически: {e}")
        else:
            self.status_label.setText(f"Ошибка: {message}")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.warning(self, "Ошибка", message)

    def update_counter(self, count):
        self.ui_manager.update_counter(count)

        # Если был запрос на новый лист — активируем создание и сбрасываем флаг
        if self.next_sheet_requested:
            try:
                self.excel_exporter.create_new_sheet()
                self.ui_manager.update_status("Создан новый лист в Excel", "color: green;")
                logger.info("Создан новый лист Excel после следующего скриншота")
            except Exception as e:
                logger.warning(f"Не удалось создать новый лист: {e}")
                self.ui_manager.update_status(f"Ошибка при создании листа: {e}", "color: red;")

            self.next_sheet_requested = False

    def update_status(self, message):
        self.ui_manager.update_status(message)

    def update_progress(self, value, visible):
        self.ui_manager.update_progress(value, visible)
    
    def closeEvent(self, event):
        self.screenshot_manager.cleanup()
        event.accept()

    def toggle_auto_open(self, state):
        """Сохраняет настройку автооткрытия Excel"""
        is_enabled = state == Qt.CheckState.Checked.value
        config.excel_auto_open = is_enabled
        config.save_to_file()
        self.ui_manager.update_status(
            f"Автооткрытие Excel {'включено' if is_enabled else 'выключено'}",
            "color: green;" if is_enabled else "color: gray;"
            )
        logger.info(f"Настройка автооткрытия Excel изменена: {is_enabled}")

    def request_next_sheet(self):
        """Создаёт новую подпапку для следующего листа"""
        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return

        try:
            self.screenshot_manager.next_group()
            current_group = self.screenshot_manager.current_group
            self.ui_manager.update_status(f"Создана новая группа: {current_group}", "color: blue;")
            logger.info(f"Создана новая группа: {current_group}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать группу: {e}")
            logger.error(f"Ошибка при создании группы: {e}")
