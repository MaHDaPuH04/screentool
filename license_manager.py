import hashlib
import json
import os
import socket
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Tuple
from logger import logger


class LicenseManager:
    """Менеджер лицензий с проверкой по IP и дневными ключами"""
    
    # Доверенные IP диапазоны (здесь не требуется лицензия)
    TRUSTED_IPS = [
        "147.108.1.",  # 147.108.1.0 - 147.108.1.255
        "127.0.0.1",   # localhost для разработки
        "192.168.",    # локальная сеть для тестирования
    ]
    
    # Секретная соль для генерации ключей - ДОЛЖНА СОВПАДАТЬ С keygen.py!
    SECRET_SALT = "AutoScreenshotTool_2024_Secret_Key_Change_This"
    
    # URL для получения точного GMT времени
    TIME_URL = "http://worldtimeapi.org/api/timezone/Etc/UTC"
    
    def __init__(self):
        self.license_file = "license.key"
        self.license_data = None
    
    def get_local_ip(self) -> str:
        """Получает реальный локальный IP-адрес машины"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.error(f"Ошибка получения IP: {e}")
            return "127.0.0.1"
    
    def is_trusted_ip(self, ip: str = None) -> bool:
        """Проверяет, является ли IP доверенным (не требует лицензии)"""
        if ip is None:
            ip = self.get_local_ip()
        
        # Точное совпадение
        if ip in self.TRUSTED_IPS:
            return True
        
        # Проверка по префиксам
        for trusted_prefix in self.TRUSTED_IPS:
            if trusted_prefix.endswith('.'):
                if ip.startswith(trusted_prefix):
                    return True
        
        # Проверка диапазона 147.108.1.0/24
        if ip.startswith("147.108.1."):
            try:
                last_octet = int(ip.split('.')[-1])
                if 0 <= last_octet <= 255:
                    return True
            except:
                pass
        
        return False
    
    def get_utc_offset(self) -> timedelta:
        """Получает смещение локального часового пояса от UTC"""
        try:
            # Пытаемся получить смещение из системы
            now_local = datetime.now()
            now_utc = datetime.now(timezone.utc)
            # Вычисляем разницу
            offset = now_local.replace(tzinfo=None) - now_utc.replace(tzinfo=None)
            return offset
        except Exception as e:
            logger.warning(f"Не удалось определить смещение часового пояса: {e}")
            return timedelta(0)
    
    def get_gmt_timestamp(self) -> int:
        """
        Получает Unix timestamp на 00:00:00 UTC текущего дня.
        Сначала пытается через интернет, при ошибке вычисляет из локального времени.
        """
        # Сначала пробуем получить через интернет
        try:
            gmt_time = self._get_online_gmt_time()
            if gmt_time:
                midnight = datetime(
                    gmt_time.year, 
                    gmt_time.month, 
                    gmt_time.day,
                    0, 0, 0,
                    tzinfo=timezone.utc
                )
                timestamp = int(midnight.timestamp())
                logger.info(f"GMT время из интернета: {midnight.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                return timestamp
        except Exception as e:
            logger.warning(f"Не удалось получить онлайн время: {e}")
        
        # Если интернета нет - вычисляем UTC из локального времени
        logger.info("Использую локальное время для вычисления UTC")
        
        # Получаем текущее локальное время
        now_local = datetime.now()
        # Получаем смещение часового пояса
        offset = self.get_utc_offset()
        
        # Вычисляем текущее UTC
        now_utc = now_local - offset
        
        # Вычисляем UTC на начало сегодняшнего дня
        midnight_utc = datetime(
            now_utc.year,
            now_utc.month,
            now_utc.day,
            0, 0, 0
        )
        
        # Добавляем обратно смещение? НЕТ, нам нужен timestamp UTC
        # midnight_utc уже в UTC, просто берем timestamp
        timestamp = int(midnight_utc.timestamp())
        
        logger.info(f"Локальное время: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Смещение от UTC: {offset}")
        logger.info(f"Вычисленное UTC: {midnight_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        logger.info(f"Timestamp для ключа: {timestamp}")
        
        return timestamp
    
    def _get_online_gmt_time(self) -> datetime:
        """Получает точное GMT время из интернета"""
        try:
            req = urllib.request.Request(
                self.TIME_URL, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                import json
                data = json.loads(response.read().decode('utf-8'))
                dt_str = data['utc_datetime']
                
                # Убираем временную зону
                if '+' in dt_str:
                    dt_str = dt_str.split('+')[0]
                elif 'Z' in dt_str:
                    dt_str = dt_str.replace('Z', '')
                
                # Убираем миллисекунды
                if '.' in dt_str:
                    dt_str = dt_str.split('.')[0]
                
                return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                
        except Exception as e:
            logger.debug(f"Ошибка получения времени: {e}")
            raise Exception("Не удалось получить время из интернета")
    
    def timestamp_to_license_key(self, timestamp: int) -> str:
        """Преобразует Unix timestamp в лицензионный ключ."""
        salted = f"{timestamp}:{self.SECRET_SALT}"
        hash_bytes = hashlib.sha256(salted.encode()).digest()
        
        # Берем первые 8 байт (64 бита) - для 4х 16-битных чисел
        numbers = []
        for i in range(0, 8, 2):
            num = (hash_bytes[i] << 8) | hash_bytes[i + 1]
            numbers.append(num)
        
        # Преобразуем в 4-значные hex строки
        key_parts = [f"{num:04X}" for num in numbers]
        
        return '-'.join(key_parts)
    
    def get_today_license_key(self) -> str:
        """Генерирует лицензионный ключ на сегодня"""
        timestamp = self.get_gmt_timestamp()
        return self.timestamp_to_license_key(timestamp)
    
    def verify_license_key(self, key: str) -> Tuple[bool, str]:
        """Проверяет лицензионный ключ. Ключ действителен ТОЛЬКО в день генерации."""
        clean_key = key.upper().replace('-', '').replace(' ', '')
        
        if len(clean_key) != 16:
            return False, "Неверный формат ключа (должно быть 16 символов)"
        
        try:
            int(clean_key, 16)
        except ValueError:
            return False, "Ключ должен содержать только hex символы (0-9, A-F)"
        
        # Получаем сегодняшний ключ
        today_key = self.get_today_license_key()
        today_clean = today_key.replace('-', '')
        
        if clean_key == today_clean:
            return True, "Лицензия действительна"
        
        return False, "Неверный или просроченный лицензионный ключ"
    
    def save_license(self, key: str) -> bool:
        """Сохраняет лицензионный ключ"""
        try:
            license_data = {
                "key": key,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "ip": self.get_local_ip()
            }
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2, ensure_ascii=False)
            logger.info("Лицензия сохранена")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения лицензии: {e}")
            return False
    
    def load_license(self) -> str:
        """Загружает сохраненную лицензию"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    self.license_data = json.load(f)
                return self.license_data.get("key", "")
        except Exception as e:
            logger.error(f"Ошибка загрузки лицензии: {e}")
        return ""
    
    def check_license(self) -> Tuple[bool, str]:
        """Основная проверка лицензии. Возвращает (разрешено, сообщение)"""
        current_ip = self.get_local_ip()
        # logger.info(f"Проверка лицензии. IP машины: {current_ip}")
        
        if self.is_trusted_ip(current_ip):
            # logger.info(f"IP {current_ip} в доверенном списке, лицензия не требуется")
            return True, "OK"
        
        # logger.info(f"IP {current_ip} не в доверенном списке, требуется лицензия")
        saved_key = self.load_license()
        
        if not saved_key:
            return False, "Требуется лицензионный ключ"
        
        is_valid, message = self.verify_license_key(saved_key)
        
        if is_valid:
            self.save_license(saved_key)
            return True, "Лицензия действительна"
        else:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            return False, message


# Глобальный экземпляр
license_manager = LicenseManager()