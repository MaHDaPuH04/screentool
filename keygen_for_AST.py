import hashlib
from datetime import datetime, timezone, timedelta

# Секретная соль - ДОЛЖНА БЫТЬ ТОЧНО ТАКОЙ ЖЕ, КАК В license_manager.py!
SECRET_SALT = "AutoScreenshotTool_2024_Secret_Key_Change_This"

def get_utc_offset() -> timedelta:
    """Получает смещение локального часового пояса от UTC"""
    try:
        now_local = datetime.now()
        now_utc = datetime.now(timezone.utc)
        offset = now_local.replace(tzinfo=None) - now_utc.replace(tzinfo=None)
        return offset
    except Exception:
        return timedelta(0)

def get_utc_timestamp():
    """Возвращает Unix timestamp на 00:00:00 UTC сегодняшнего дня"""
    # Получаем текущее локальное время
    now_local = datetime.now()
    # Получаем смещение часового пояса
    offset = get_utc_offset()
    
    # Вычисляем текущее UTC
    now_utc = now_local - offset
    
    # Вычисляем UTC на начало сегодняшнего дня
    midnight_utc = datetime(
        now_utc.year,
        now_utc.month,
        now_utc.day,
        0, 0, 0
    )
    
    return int(midnight_utc.timestamp())

def generate_license_key():
    """Генерирует лицензионный ключ на сегодня"""
    timestamp = get_utc_timestamp()
    salted = f"{timestamp}:{SECRET_SALT}"
    hash_bytes = hashlib.sha256(salted.encode()).digest()
    
    # Берем первые 8 байт, превращаем в 4 числа по 16 бит
    numbers = []
    for i in range(0, 8, 2):
        num = (hash_bytes[i] << 8) | hash_bytes[i + 1]
        numbers.append(num)
    
    # Форматируем как XXXX-XXXX-XXXX-XXXX
    key_parts = [f"{num:04X}" for num in numbers]
    return '-'.join(key_parts)

if __name__ == "__main__":
    key = generate_license_key()
    now_local = datetime.now()
    offset = get_utc_offset()
    now_utc = now_local - offset
    
    print("\n" + "="*60)
    print(f"ЛИЦЕНЗИОННЫЙ КЛЮЧ НА {now_utc.strftime('%Y-%m-%d')} (UTC)")
    print("="*60)
    print(f"\n  {key}\n")
    print("="*60)
    print(f"Локальное время: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Смещение от UTC: {offset}")
    print(f"UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)