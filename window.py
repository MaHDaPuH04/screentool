from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QCheckBox, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from resource_path import resource_path
from PyQt6.QtGui import QFont, QIcon
import shot
import os
from datetime import datetime
from excelexport import ExcelExporter
from logger import logger
from config import config
from dialogs import CleanupDialog
from ui_manager import UIManager
from file_manager import FileManager
from database import db_manager
from help_dialog import HelpDialog


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
        
        # Данные из БД
        self.well_data = None
        self.selected_report_type = "PreRun"  # По умолчанию
        
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
        self.screenshot_manager.show_preview_requested.connect(self.handle_preview_request)

        #СИГНАЛ ДЛЯ ПРЕВЬЮ
        self.screenshot_manager.show_preview_requested.connect(self.handle_preview_request)

        # Загружаем данные из БД при запуске
        self.load_well_data()

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
        self.setWindowTitle(f"Auto Screenshot Tool v 1.0.7")
        self.setFixedSize(500, 550)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # === ЗАГОЛОВОЧНАЯ СТРОКА С КНОПКОЙ СПРАВКИ ===
        header_layout = QHBoxLayout()

        # Заголовок
        title_label = QLabel("Auto Screenshot Tool")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Кнопка справки
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(30, 30)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: #0000FF;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00BFFF;
            }
        """)
        self.help_btn.setToolTip("Открыть справку")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.help_btn)
        
        layout.addLayout(header_layout)

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

        # === ГРУППА ДЛЯ ВЫБОРА ПАПКИ И КНОПКИ "СЛЕДУЮЩИЙ ЛИСТ" ===
        folder_group = QGroupBox("Папка сохранения и лист Excel")
        folder_layout = QVBoxLayout()

        # Строка с выбором типа отчета
        report_type_layout = QHBoxLayout()
        report_type_layout.addWidget(QLabel("Тип отчета:"))
        self.report_type_combo = QComboBox()
        for key, value in config.report_types.items():
            self.report_type_combo.addItem(value, key)
        self.report_type_combo.currentIndexChanged.connect(self.update_preview_path)
        report_type_layout.addWidget(self.report_type_combo)
        folder_layout.addLayout(report_type_layout)

        # Превью пути
        self.path_preview_label = QLabel("Путь будет создан: ...")
        self.path_preview_label.setWordWrap(True)
        self.path_preview_label.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        folder_layout.addWidget(self.path_preview_label)

        # Кнопки в одной строке
        buttons_row_layout = QHBoxLayout()

        # Кнопка автоматического пути
        self.auto_folder_btn = QPushButton("Подтвердить выбор папки")
        self.auto_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.auto_folder_btn.setToolTip("Создать папку автоматически на основе данных БД")

        # Кнопка ручного выбора
        self.manual_folder_btn = QPushButton("Выбрать вручную")
        self.manual_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.manual_folder_btn.setToolTip("Выбрать папку вручную")

        # Кнопка "Следующий лист"
        self.next_sheet_btn = QPushButton("Следующий лист")
        self.next_sheet_btn.setStyleSheet("""
            QPushButton {
                background-color: #696969;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.next_sheet_btn.setToolTip("Следующие скриншоты будут добавлены на новый лист Excel")

        buttons_row_layout.addWidget(self.auto_folder_btn)
        buttons_row_layout.addWidget(self.manual_folder_btn)
        buttons_row_layout.addWidget(self.next_sheet_btn)

        folder_layout.addLayout(buttons_row_layout)

        # Информация о текущей папке
        self.folder_label = QLabel("Папка сохранения: не выбрана")
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet("font-size: 9pt;")
        folder_layout.addWidget(self.folder_label)

        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Счетчик скриншотов
        self.counter_label = QLabel("Сделано скриншотов: 0")
        layout.addWidget(self.counter_label)

        # ГРУППА ДЛЯ двух КНОПОК
        buttons_group = QGroupBox("Действия")
        buttons_layout = QHBoxLayout()

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
                                         
        buttons_layout.addWidget(self.excel_btn)
        buttons_layout.addWidget(self.vm_btn)
    
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
        # Существующие сигналы
        self.capture_checkbox.stateChanged.connect(self.toggle_capture)
        self.hotkey_checkbox.stateChanged.connect(self.toggle_hotkey)
        self.delete_last_checkbox.stateChanged.connect(self.toggle_delete_last)
        self.manual_folder_btn.clicked.connect(self.select_folder_manual)
        self.auto_folder_btn.clicked.connect(self.select_folder_auto)
        self.excel_btn.clicked.connect(self.export_to_excel)
        self.vm_btn.clicked.connect(self.clear_screenshots_folder)
        self.auto_open_check.stateChanged.connect(self.toggle_auto_open)
        self.next_sheet_btn.clicked.connect(self.request_next_sheet)
        self.help_btn.clicked.connect(self.show_help)

        # Сигналы от менеджера скриншотов
        self.screenshot_manager.screenshot_taken.connect(self.update_counter)
        self.screenshot_manager.status_changed.connect(self.update_status)
        self.screenshot_manager.progress_changed.connect(self.update_progress)
        self.screenshot_manager.capture_error_detected.connect(self.show_capture_error)

    def load_well_data(self):
        """Загружает данные по скважине из БД"""
        if db_manager.is_connected:
            self.well_data = db_manager.get_well_data()
            if self.well_data:
                self.ui_manager.update_status("Данные по скважине загружены", "color: green;")
                self.update_preview_path()
            else:
                self.ui_manager.update_status("Данные по скважине не найдены", "color: orange;")
        else:
            self.ui_manager.update_status("Нет подключения к БД", "color: orange;")

    def update_preview_path(self):
        """Обновляет превью пути на основе выбранного типа отчета"""
        if not self.well_data:
            self.path_preview_label.setText("Нет данных по скважине")
            return
            
        report_type_key = self.report_type_combo.currentData()
        self.selected_report_type = config.report_types[report_type_key]
        
        # Получаем данные
        annu_name = self.well_data.get('ANNU_NAME', 'ANNU_NAME')
        path_name = self.well_data.get('PATH_NAME', 'PATH_NAME')
        run_num = self.well_data.get('MWTI_RUN_NO', 'RUN_NUM')
        use_path = self.well_data.get('USE_PATH_IN_NAME', True)
        
        # Проверяем, содержит ли PATH_NAME "Orig Path"
        if path_name and "Orig Path" in path_name:
            use_path = False
        
        # Формируем путь в зависимости от USE_PATH_IN_NAME
        if use_path:
            # Используем PATH в пути
            if self.selected_report_type == "Custom":
                preview = f"D:\\Wells\\{annu_name}\\{path_name}\\Run_{run_num} (Custom)"
            else:
                preview = f"D:\\Wells\\{annu_name}\\{path_name}\\Run_{run_num}\\{self.selected_report_type}"
        else:
            # Не используем PATH в пути
            if self.selected_report_type == "Custom":
                preview = f"D:\\Wells\\{annu_name}\\Run_{run_num} (Custom)"
            else:
                preview = f"D:\\Wells\\{annu_name}\\Run_{run_num}\\{self.selected_report_type}"
        
        self.path_preview_label.setText(f"Путь будет создан: {preview}")

    def select_folder_auto(self):
        """Создает папку по автоматическому пути на основе данных БД"""
        if not self.well_data:
            QMessageBox.warning(self, "Ошибка", "Нет данных по скважине из БД!")
            return

        report_type = self.selected_report_type
        
        # Получаем данные
        annu_name = self.well_data.get('ANNU_NAME', '')
        path_name = self.well_data.get('PATH_NAME', '')
        run_num = self.well_data.get('MWTI_RUN_NO', '')
        use_path = self.well_data.get('USE_PATH_IN_NAME', True)
        
        if not annu_name:
            QMessageBox.warning(self, "Ошибка", "Не найдено имя скважины (ANNU_NAME) в БД!")
            return
        
        # Проверяем, содержит ли PATH_NAME "Orig Path"
        if path_name and "Orig Path" in path_name:
            use_path = False
        
        # Формируем базовый путь
        base_path = f"D:\\Wells\\{annu_name}"
        
        # Формируем полный путь в зависимости от use_path
        if use_path:
            # Используем PATH в пути
            if report_type == "Custom":
                folder_path = os.path.join(base_path, path_name, f"Run_{run_num}")
            else:
                folder_path = os.path.join(base_path, path_name, f"Run_{run_num}", report_type)
        else:
            # Не используем PATH в пути
            if report_type == "Custom":
                folder_path = os.path.join(base_path, f"Run_{run_num}")
            else:
                folder_path = os.path.join(base_path, f"Run_{run_num}", report_type)

        # Создаем папку
        try:
            os.makedirs(folder_path, exist_ok=True)
            success = self.screenshot_manager.set_save_path(folder_path)
            
            if success:
                self.folder_label.setText(f"Папка сохранения: {folder_path}")
                self.ui_manager.reset_ui_after_folder_selection()
                self.ui_manager.update_status(f"Создана папка: {os.path.basename(folder_path)}", "color: green;")
            else:
                self.ui_manager.show_folder_selection_error()
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку: {str(e)}")

    def select_folder_manual(self):
        """Ручной выбор папки (старая функциональность)"""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder:
            success = self.screenshot_manager.set_save_path(folder)
            if success:
                self.folder_label.setText(f"Папка сохранения: {folder}")
                self.ui_manager.reset_ui_after_folder_selection()
            else:
                self.ui_manager.show_folder_selection_error()

    def generate_excel_name(self):
        """Генерирует имя для Excel файла на основе данных БД"""
        try:
            if self.well_data and self.selected_report_type != "Custom":
                # Получаем данные
                path_name = self.well_data.get('PATH_NAME', '')
                annu_name = self.well_data.get('ANNU_NAME', '')
                run_num = self.well_data.get('MWTI_RUN_NO', 'RUN_NUM')
                use_path = self.well_data.get('USE_PATH_IN_NAME', True)
                
                # Проверяем, содержит ли PATH_NAME "Orig Path"
                if path_name and "Orig Path" in path_name:
                    use_path = False
                
                if use_path:
                    # Используем PATH в имени файла
                    excel_name = (f"{self.selected_report_type}_{run_num}_"
                                f"{self.well_data['OOIN_NAME']}_"
                                f"{self.well_data['FCTY_NAME']}_"
                                f"{annu_name}_"
                                f"{path_name}.xlsx")
                else:
                    # Не используем PATH в имени файла
                    excel_name = (f"{self.selected_report_type}_{run_num}_"
                                f"{self.well_data['OOIN_NAME']}_"
                                f"{self.well_data['FCTY_NAME']}_"
                                f"{annu_name}.xlsx")
                
                self.ui_manager.update_status("Имя сгенерировано из БД", "color: blue;")
                return excel_name
            else:
                # Для Custom или при отсутствии данных - стандартное имя
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                default_name = f"screenshots_export_{timestamp}.xlsx"
                self.ui_manager.update_status("Имя сгенерировано по умолчанию", "color: gray;")
                return default_name
                
        except Exception as e:
            logger.error(f"Ошибка генерации имени: {e}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"screenshots_export_{timestamp}.xlsx"

    def export_to_excel(self):
        """Экспорт в Excel с именем из БД"""
        print("=== НАЧАТА КНОПКА ЭКСПОРТА ===")

        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения!")
            return

        # Генерируем имя файла
        excel_name = self.generate_excel_name()
        
        export_folder = self.screenshot_manager.base_save_path if hasattr(self.screenshot_manager, 'base_save_path') else self.screenshot_manager.save_path
    
        print(f"Экспортируем из папки: {export_folder}")
        print(f"Имя Excel файла: {excel_name}")

        default_excel = os.path.join(export_folder, excel_name)

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

    def update_counter(self, count):
        self.ui_manager.update_counter(count)
        
        # ОБНОВЛЯЕМ ПРЕВЬЮ ЕСЛИ ОНО ОТКРЫТО - В ГЛАВНОМ ПОТОКЕ
        if hasattr(self.screenshot_manager, 'update_preview'):
            self.screenshot_manager.update_preview(count)

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

    def handle_preview_request(self, image_path, screenshot_count):
        """Обрабатывает запрос на показ превью - В ГЛАВНОМ ПОТОКЕ UI"""
        try:
            self.screenshot_manager.show_preview_dialog(image_path, screenshot_count)
        except Exception as e:
            logger.error(f"Ошибка обработки запроса превью: {e}")

    def show_help(self):
        """Показывает диалог справки"""
        try:
            help_dialog = HelpDialog(self)
            help_dialog.exec()
        except Exception as e:
            logger.error(f"Ошибка открытия справки: {e}")
            QMessageBox.warning(self, "Ошибка", "Не удалось открыть справку")
