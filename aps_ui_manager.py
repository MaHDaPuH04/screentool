import os
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QTimer
from logger import logger
from config import config
from aps_database import aps_db_manager


class APSUIManager:
    """Менеджер UI для вкладки APS"""
    
    def __init__(self, main_window, screenshot_manager):
        self.main_window = main_window
        self.screenshot_manager = screenshot_manager
        self.well_data = None
        self.selected_report_key = 2
        self.selected_report_type = "PreRun"
        self.export_successful = False
        self.is_running = False
        self.excel_exporter = None
        
        # Пытаемся подключиться к APS БД при инициализации
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Подключается к APS БД (можно указать путь к файлу)"""
        # TODO: Укажите правильный путь к вашему файлу SQLite
        db_path = "aps_data.db"  # Замените на реальный путь
        
        if aps_db_manager.connect(db_path):
            # Для отладки - выводим список таблиц
            aps_db_manager.get_table_list()
        else:
            logger.warning(f"Не удалось подключиться к APS БД по пути: {db_path}")
    
    def set_excel_exporter(self, exporter):
        """Устанавливает экспортер Excel"""
        self.excel_exporter = exporter
    
    def load_well_data(self):
        """Загружает данные из APS SQLite базы"""
        if aps_db_manager.is_connected:
            self.well_data = aps_db_manager.get_well_data()
            if self.well_data:
                self.main_window.ui_manager.update_status("APS: Данные загружены из SQLite", "color: green;")
                self.update_preview_path()
                return True
            else:
                self.main_window.ui_manager.update_status("APS: Данные не найдены", "color: orange;")
                return False
        else:
            # Используем тестовые данные
            self.well_data = aps_db_manager._get_mock_data()
            self.main_window.ui_manager.update_status("APS: Используются тестовые данные (нет БД)", "color: orange;")
            self.update_preview_path()
            return False
    
    def update_preview_path(self):
        """Обновляет превью пути для APS"""
        if not self.well_data:
            self.main_window.path_preview_label_aps.setText("Нет данных по скважине APS")
            return
        
        report_type_display = self.selected_report_type
        
        annu_name = self.well_data.get('ANNU_NAME', 'ANNU_NAME')
        path_name = self.well_data.get('PATH_NAME', 'PATH_NAME')
        run_num = self.well_data.get('MWTI_RUN_NO', 'RUN_NUM')
        use_path = self.well_data.get('USE_PATH_IN_NAME', True)
        
        if path_name and "Orig Path" in path_name:
            use_path = False
        
        if use_path:
            if report_type_display == "Custom":
                preview = f"D:\\APS_Wells\\{annu_name}\\{path_name}\\Run_{run_num} (Custom)"
            else:
                preview = f"D:\\APS_Wells\\{annu_name}\\{path_name}\\Run_{run_num}\\{report_type_display}"
        else:
            if report_type_display == "Custom":
                preview = f"D:\\APS_Wells\\{annu_name}\\Run_{run_num} (Custom)"
            else:
                preview = f"D:\\APS_Wells\\{annu_name}\\Run_{run_num}\\{report_type_display}"
        
        self.main_window.path_preview_label_aps.setText(f"Путь будет создан: {preview}")
    
    def select_folder_auto(self):
        """Создаёт папку по автоматическому пути для APS"""
        if not self.well_data:
            QMessageBox.warning(self.main_window, "Ошибка", "Нет данных по скважине из APS БД!")
            return
        
        report_type_display = self.selected_report_type
        
        annu_name = self.well_data.get('ANNU_NAME', '')
        path_name = self.well_data.get('PATH_NAME', '')
        run_num = self.well_data.get('MWTI_RUN_NO', '')
        use_path = self.well_data.get('USE_PATH_IN_NAME', True)
        
        if not annu_name:
            QMessageBox.warning(self.main_window, "Ошибка", "Не найдено имя скважины в APS БД!")
            return
        
        if path_name and "Orig Path" in path_name:
            use_path = False
        
        base_path = f"D:\\APS_Wells\\{annu_name}"
        
        if use_path:
            if report_type_display == "Custom":
                folder_path = os.path.join(base_path, path_name, f"Run_{run_num}")
            else:
                folder_path = os.path.join(base_path, path_name, f"Run_{run_num}", report_type_display)
        else:
            if report_type_display == "Custom":
                folder_path = os.path.join(base_path, f"Run_{run_num}")
            else:
                folder_path = os.path.join(base_path, f"Run_{run_num}", report_type_display)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            success = self.screenshot_manager.set_save_path(folder_path)
            
            if success:
                self.main_window.folder_label_aps.setText(f"Папка сохранения: {folder_path}")
                self.main_window.group_label_aps.setText("Папка не создана (нажмите 'Запустить')")
                self.export_successful = False
                self.main_window.vm_btn_aps.setEnabled(False)
                self.main_window.vm_btn_aps.setToolTip("Сначала выполните экспорт в Excel")
                
                if self.is_running:
                    self.toggle_run()
                
                self.main_window.ui_manager.update_status(f"APS: Выбрана папка {os.path.basename(folder_path)}", "color: green;")
            else:
                QMessageBox.warning(self.main_window, "Ошибка", "Не удалось установить папку для сохранения")
                
        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось создать папку: {str(e)}")
    
    def select_folder_manual(self):
        """Ручной выбор папки для APS"""
        folder = QFileDialog.getExistingDirectory(self.main_window, "Выберите папку для сохранения APS")
        if folder:
            success = self.screenshot_manager.set_save_path(folder)
            if success:
                self.main_window.folder_label_aps.setText(f"Папка сохранения: {folder}")
                self.main_window.group_label_aps.setText("Папка не создана (нажмите 'Запустить')")
                self.export_successful = False
                self.main_window.vm_btn_aps.setEnabled(False)
                self.main_window.vm_btn_aps.setToolTip("Сначала выполните экспорт в Excel")
                
                if self.is_running:
                    self.toggle_run()
                
                self.main_window.ui_manager.update_status(f"APS: Выбрана папка {os.path.basename(folder)}", "color: green;")
            else:
                self.main_window.ui_manager.show_folder_selection_error()
    
    def generate_excel_name(self):
        """Генерирует имя для Excel файла APS"""
        try:
            if self.well_data and self.selected_report_type != "Custom":
                path_name = self.well_data.get('PATH_NAME', '')
                annu_name = self.well_data.get('ANNU_NAME', '')
                run_num = self.well_data.get('MWTI_RUN_NO', 'RUN_NUM')
                use_path = self.well_data.get('USE_PATH_IN_NAME', True)
                
                if path_name and "Orig Path" in path_name:
                    use_path = False
                
                report_type_display = self.selected_report_type
                
                if use_path:
                    excel_name = f"APS_{report_type_display}_{run_num}_{annu_name}_{path_name}.xlsx"
                else:
                    excel_name = f"APS_{report_type_display}_{run_num}_{annu_name}.xlsx"
                
                return excel_name
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                return f"APS_screenshots_export_{timestamp}.xlsx"
                
        except Exception as e:
            logger.error(f"Ошибка генерации имени APS: {e}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"APS_screenshots_export_{timestamp}.xlsx"
    
    def export_to_excel(self):
        """Экспорт в Excel для APS"""
        if not self.screenshot_manager.save_path:
            QMessageBox.warning(self.main_window, "Ошибка", "Сначала выберите папку для сохранения!")
            return
        
        excel_name = self.generate_excel_name()
        export_folder = self.screenshot_manager.base_save_path if hasattr(self.screenshot_manager, 'base_save_path') else self.screenshot_manager.save_path
        default_excel = os.path.join(export_folder, excel_name)
        
        excel_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Сохранить Excel файл APS",
            default_excel,
            "Excel Files (*.xlsx)"
        )
        
        if not excel_path:
            return
        
        self.main_window.excel_btn_aps.setEnabled(False)
        self.main_window.progress_bar_aps.setVisible(True)
        self.main_window.status_label_aps.setText("Экспорт в Excel APS...")
        
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            result_path, message = self.excel_exporter.export_screenshots_to_excel(
                export_folder,
                excel_path
            )
        except Exception as e:
            error_msg = f"Исключение: {str(e)}"
            self.main_window.status_label_aps.setText(error_msg)
            self.main_window.status_label_aps.setStyleSheet("color: red;")
            QMessageBox.critical(self.main_window, "Ошибка APS", error_msg)
            result_path = None
            message = error_msg
        
        finally:
            self.main_window.progress_bar_aps.setVisible(False)
            self.main_window.excel_btn_aps.setEnabled(True)
            QTimer.singleShot(3000, lambda: self.main_window.status_label_aps.setStyleSheet(""))
        
        if result_path:
            self.main_window.status_label_aps.setText(f"Успешно: {os.path.basename(result_path)}")
            self.main_window.status_label_aps.setStyleSheet("color: green; font-weight: bold;")
            
            self.export_successful = True
            self.main_window.vm_btn_aps.setEnabled(True)
            
            # ✅ МЕНЯЕМ СТИЛЬ КНОПКИ НА АКТИВНЫЙ (как в Advantage)
            self.main_window.vm_btn_aps.setStyleSheet("""
                QPushButton {
                    background-color: #696969;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #A0A0A0;
                }
                QPushButton:pressed {
                    background-color: #808080;
                }
            """)
            self.main_window.vm_btn_aps.setToolTip("Очистить папку от скриншотов APS")
            
            QMessageBox.information(self.main_window, "Успех APS", f"Создан файл:\n{os.path.basename(result_path)}")
            
            # Автоматическое открытие Excel
            if config.excel_auto_open:
                try:
                    os.startfile(result_path)
                    logger.info(f"APS: Автоматически открыт Excel файл: {result_path}")
                    self.main_window.ui_manager.update_status("APS: Excel файл открыт автоматически", "color: green;")
                except Exception as e:
                    logger.warning(f"APS: Не удалось открыть Excel автоматически: {e}")
                    self.main_window.ui_manager.update_status("APS: Не удалось открыть Excel автоматически", "color: orange;")
            
        else:
            self.main_window.status_label_aps.setText(f"Ошибка: {message}")
            self.main_window.status_label_aps.setStyleSheet("color: red;")
            self.main_window.vm_btn_aps.setEnabled(False)
            self.main_window.vm_btn_aps.setStyleSheet("""
                QPushButton {
                    background-color: #C0C0C0;
                    color: #757575;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            self.main_window.vm_btn_aps.setToolTip("Сначала выполните успешный экспорт в Excel")
            QMessageBox.warning(self.main_window, "Ошибка APS", message)
    
    def toggle_run(self):
        """Запускает/останавливает функции APS"""
        if not self.is_running:
            if not self.screenshot_manager.save_path:
                if self.screenshot_manager.base_save_path:
                    try:
                        new_group_path = os.path.join(
                            self.screenshot_manager.base_save_path,
                            self.screenshot_manager.current_group
                        )
                        os.makedirs(new_group_path, exist_ok=True)
                        self.screenshot_manager.save_path = new_group_path
                        self.main_window.group_label_aps.setText(f"Текущий лист: {self.screenshot_manager.current_group}")
                    except Exception as e:
                        QMessageBox.warning(self.main_window, "Ошибка", f"Не удалось создать папку: {str(e)}")
                        return
                else:
                    QMessageBox.warning(self.main_window, "Ошибка", "Сначала выберите папку для сохранения APS!")
                    return
            
            # Включаем захват
            self.screenshot_manager.capture_enabled = True
            
            # Включаем горячие клавиши
            self.screenshot_manager.enable_hotkey()
            
            # Устанавливаем флаги через UI (чтобы чекбоксы отображали состояние)
            self.main_window.capture_checkbox_aps.setChecked(True)
            self.main_window.hotkey_checkbox_aps.setChecked(True)
            self.main_window.delete_last_checkbox_aps.setChecked(True)
            self.main_window.auto_open_check_aps.setChecked(config.excel_auto_open)
            
            # Включаем флаг удаления
            self.main_window.aps_delete_enabled = True
            
            self.is_running = True
            self.main_window.run_btn_aps.setText("Остановить")
            self.main_window.run_btn_aps.setStyleSheet("""
                QPushButton {
                    background-color: #E76F51;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { opacity: 0.9; }
            """)
            self.main_window.ui_manager.update_status("APS: ✅ Программа запущена", "color: green;")
        else:
            # Выключаем захват
            self.screenshot_manager.capture_enabled = False
            
            # Выключаем горячие клавиши
            self.screenshot_manager.disable_hotkey()
            
            # Сбрасываем флаги через UI
            self.main_window.capture_checkbox_aps.setChecked(False)
            self.main_window.hotkey_checkbox_aps.setChecked(False)
            self.main_window.delete_last_checkbox_aps.setChecked(False)
            # auto_open_check_aps НЕ выключаем, сохраняем настройку
            
            # Выключаем флаг удаления
            self.main_window.aps_delete_enabled = False
            
            self.is_running = False
            self.main_window.run_btn_aps.setText("Запустить")
            self.main_window.run_btn_aps.setStyleSheet("""
                QPushButton {
                    background-color: #2A9D8F;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { opacity: 0.9; }
            """)
            self.main_window.ui_manager.update_status("APS: ⏹ Программа остановлена", "color: gray;")
            
    def on_report_type_changed(self, index):
        """Обработчик изменения типа отчета APS"""
        self.selected_report_key = self.main_window.report_type_combo_aps.currentData()
        self.selected_report_type = self.main_window.report_types.get(self.selected_report_key, "Custom")
        logger.info(f"APS тип отчета изменен: ключ={self.selected_report_key}, значение={self.selected_report_type}")
        self.load_well_data()