#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех компонентов Auto Screenshot Tool
"""
import sys
import os

def test_imports():
    """Тестирует импорт всех модулей"""
    print("Тестирование импортов...")
    
    try:
        import config
        print("config.py - OK")
    except Exception as e:
        print(f"config.py - ОШИБКА: {e}")
        return False
    
    try:
        import logger
        print("logger.py - OK")
    except Exception as e:
        print(f"logger.py - ОШИБКА: {e}")
        return False
    
    try:
        import vm_scanner
        print("vm_scanner.py - OK")
    except Exception as e:
        print(f"vm_scanner.py - ОШИБКА: {e}")
        return False
    
    try:
        import settings_dialog
        print("settings_dialog.py - OK")
    except Exception as e:
        print(f"settings_dialog.py - ОШИБКА: {e}")
        return False
    
    try:
        import shot
        print("shot.py - OK")
    except Exception as e:
        print(f"shot.py - ОШИБКА: {e}")
        return False
    
    try:
        import window
        print("window.py - OK")
    except Exception as e:
        print(f"window.py - ОШИБКА: {e}")
        return False
    
    try:
        import excelexport
        print("excelexport.py - OK")
    except Exception as e:
        print(f"excelexport.py - ОШИБКА: {e}")
        return False
    
    try:
        import main
        print("main.py - OK")
    except Exception as e:
        print(f"main.py - ОШИБКА: {e}")
        return False
    
    return True

def test_config():
    """Тестирует конфигурацию"""
    print("\nТестирование конфигурации...")
    
    try:
        from config import config
        print(f"Качество скриншотов: {config.screenshot_quality}")
        print(f"Формат скриншотов: {config.screenshot_format}")
        print(f"Минимальный интервал: {config.min_interval}")
        print(f"Максимальное количество: {config.max_screenshots}")
        print(f"Порты для сканирования: {config.vm_scan_ports}")
        print(f"Горячие клавиши: {config.hotkeys}")
        return True
    except Exception as e:
        print(f"Ошибка конфигурации: {e}")
        return False

def test_logger():
    """Тестирует логгер"""
    print("\nТестирование логгера...")
    
    try:
        from logger import logger
        logger.info("Тестовое сообщение")
        logger.warning("Тестовое предупреждение")
        logger.error("Тестовая ошибка")
        print("Логгер работает корректно")
        return True
    except Exception as e:
        print(f"Ошибка логгера: {e}")
        return False

def test_vm_scanner():
    """Тестирует сканер VM"""
    print("\nТестирование сканера VM...")
    
    try:
        from vm_scanner import vm_scanner
        # Тестируем сканирование локального хоста
        result = vm_scanner.scan_port("127.0.0.1", 80, timeout=1)
        print(f"Сканер VM работает (тест порта 80: {result})")
        return True
    except Exception as e:
        print(f"Ошибка сканера VM: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Запуск тестирования Auto Screenshot Tool")
    print("=" * 50)
    
    # Тестируем импорты
    if not test_imports():
        print("\nТестирование импортов провалено!")
        return False
    
    # Тестируем конфигурацию
    if not test_config():
        print("\nТестирование конфигурации провалено!")
        return False
    
    # Тестируем логгер
    if not test_logger():
        print("\nТестирование логгера провалено!")
        return False
    
    # Тестируем сканер VM
    if not test_vm_scanner():
        print("\nТестирование сканера VM провалено!")
        return False
    
    print("\n" + "=" * 50)
    print("Все тесты пройдены успешно!")
    print("Приложение готово к запуску!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
