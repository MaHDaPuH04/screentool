"""
Конфигурационный файл для Auto Screhot Tool
"""
import os
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class AppConfig:
    """Основные настройки приложения"""
    
    # Настройки скриншотов
    screenshot_quality: int = 85
    screenshot_format: str = "PNG"
    min_interval: float = 0.8
    max_screenshots: int = 1000
    
    # Настройки окна
    window_capture_offset: Tuple[int, int, int, int] = (8, 1, -8, -13)
    
    # Настройки VM
    vm_base_ip: str = "10.7.128"
    vm_default_port: int = 50000
    vm_scan_ports: List[int] = None
    vm_timeout: int = 5
    
    # Настройки Excel
    excel_auto_open: bool = True
    
    # Настройки логирования
    log_level: str = "INFO"
    log_file: str = "screenshot_tool.log"
    log_max_size: int = 10 * 1024 * 1024
    log_backup_count: int = 3
    
    # Настройки UI
    window_width: int = 500
    window_height: int = 400
    theme: str = "Fusion"
    
    # Горячие клавиши
    hotkeys: List[str] = None

    # Настройки БД
    db_server: str = ""
    db_database: str = "advantage"
    db_use_windows_auth: bool = True

    # Список серверов для автоматического выбора
    db_servers_to_try: List[str] = None
    
    # Таймаут подключения к БД (секунды)
    db_connection_timeout: int = 1
    
    # Словарь типов отчетов
    report_types: dict = None

    def __post_init__(self):
        """Инициализация значений по умолчанию"""
        if self.vm_scan_ports is None:
            self.vm_scan_ports = [50000, 50001, 50002, 50003, 50004]
        if self.hotkeys is None:
            self.hotkeys = ["print screen", "insert"]
        if self.report_types is None:
            self.report_types = {
                1: "PreTIP",
                2: "PreRun", 
                3: "PostRun",
                4: "Custom"
            }
        if self.db_servers_to_try is None:
            self.db_servers_to_try = [
                "ADVMWD1\\ADVANTAGE2017",
                "ADVMWD2\\ADVANTAGE2017",
                "TyuMWD212\\ADVANTAGE2017"
            ]

    @classmethod
    def load_from_file(cls, config_path: str = "config.json"):
        import json
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
        return cls()
    
    def save_to_file(self, config_path: str = "config.json"):
        import json
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

config = AppConfig.load_from_file()