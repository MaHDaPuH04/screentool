"""
Централизованная система логирования для Auto Screenshot Tool
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import config

class ScreenshotLogger:
    """Централизованный логгер для приложения"""
    
    def __init__(self):
        self.logger = logging.getLogger('ScreenshotTool')
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Обработчик для файла с ротацией
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = RotatingFileHandler(
            os.path.join('logs', config.log_file),
            maxBytes=config.log_max_size,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Логирование отладочной информации"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Логирование информационных сообщений"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Логирование предупреждений"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Логирование ошибок"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Логирование критических ошибок"""
        self.logger.critical(message)
    
    def screenshot_taken(self, filename: str, mode: str):
        """Специальное логирование для скриншотов"""
        self.info(f"Скриншот {mode} сохранен: {filename}")
    
    def excel_export(self, filepath: str, count: int):
        """Специальное логирование для экспорта в Excel"""
        self.info(f"Excel экспорт: {filepath} ({count} скриншотов)")
    
    def vm_connection(self, ip: str, port: int, success: bool):
        """Специальное логирование для подключения к VM"""
        status = "успешно" if success else "неудачно"
        self.info(f"Подключение к VM {ip}:{port} - {status}")
    
    def performance(self, operation: str, duration: float):
        """Логирование производительности"""
        self.debug(f"Производительность: {operation} заняло {duration:.3f} сек")

# Глобальный экземпляр логгера
logger = ScreenshotLogger()

