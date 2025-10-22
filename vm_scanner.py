"""
Модуль для автоматического определения порта VM
"""
import os
import socket
import threading
import time
from typing import List, Tuple, Optional
from config import config
from logger import logger

class VMScanner:
    """Сканер для определения доступных портов VM"""
    
    def __init__(self):
        self.available_ports = []
        self.scan_results = {}
    
    def scan_port(self, ip: str, port: int, timeout: int = 2) -> bool:
        """Проверяет доступность конкретного порта"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                return result == 0
        except Exception as e:
            logger.debug(f"Ошибка сканирования порта {port}: {e}")
            return False
    
    def scan_ports_parallel(self, ip: str, ports: List[int], timeout: int = 2) -> List[int]:
        """Сканирует несколько портов параллельно"""
        available_ports = []
        threads = []
        results = {}
        
        def check_port(port):
            results[port] = self.scan_port(ip, port, timeout)
        
        # Запускаем проверку портов в отдельных потоках
        for port in ports:
            thread = threading.Thread(target=check_port, args=(port,))
            thread.start()
            threads.append(thread)
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Собираем результаты
        for port, is_open in results.items():
            if is_open:
                available_ports.append(port)
                logger.info(f"Порт {port} доступен на {ip}")
        
        return available_ports
    
    def find_best_vm_port(self, ip_part: str) -> Optional[Tuple[str, int]]:
        """Находит лучший доступный порт для VM"""
        full_ip = f"{config.vm_base_ip}.{ip_part}"
        logger.info(f"Сканирование VM {full_ip}...")
        
        # Сканируем порты
        available_ports = self.scan_ports_parallel(full_ip, config.vm_scan_ports, config.vm_timeout)
        
        if not available_ports:
            logger.warning(f"Не найдено доступных портов для {full_ip}")
            return None
        
        # Выбираем первый доступный порт (обычно это основной)
        best_port = available_ports[0]
        logger.info(f"Выбран порт {best_port} для {full_ip}")
        
        return full_ip, best_port
    
    def test_vm_connection(self, ip: str, port: int) -> bool:
        """Тестирует подключение к VM"""
        try:
            # Пробуем подключиться к общему ресурсу
            test_path = f"\\\\{ip}\\C$"
            return os.path.exists(test_path)
        except Exception as e:
            logger.debug(f"Ошибка тестирования подключения к {ip}:{port}: {e}")
            return False
    
    def get_vm_path(self, ip_part: str) -> Optional[str]:
        """Получает путь к VM с автоматическим определением порта"""
        try:
            result = self.find_best_vm_port(ip_part)
            if result:
                ip, port = result
                # Формируем путь с найденным портом
                vm_path = f"\\\\{ip}\\C$\\Users\\ADVMANAGER\\Desktop\\WORK FOLDER"
                logger.info(f"Путь к VM: {vm_path}")
                return vm_path
            else:
                logger.error(f"Не удалось найти доступный порт для VM {ip_part}")
                return None
        except Exception as e:
            logger.error(f"Ошибка определения пути к VM: {e}")
            return None

# Глобальный экземпляр сканера
vm_scanner = VMScanner()
