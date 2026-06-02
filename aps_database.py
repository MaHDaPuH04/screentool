import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any
from logger import logger


class APSDatabaseManager:
    """Менеджер базы данных APS (SQLite)"""
    
    def __init__(self, db_path: str = "aps_data.db"):
        """
        Инициализация менеджера APS БД
        
        Args:
            db_path: путь к SQLite файлу базы данных
        """
        self.db_path = db_path
        self.connection = None
        self.is_connected = False
    
    def connect(self, db_path: str = None) -> bool:
        """
        Подключение к SQLite базе данных
        
        Args:
            db_path: путь к файлу БД (если None, используем сохранённый)
        """
        if db_path:
            self.db_path = db_path
        
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Файл БД не найден: {self.db_path}")
                return False
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.is_connected = True
            logger.info(f"✅ Подключено к APS БД: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к APS БД: {e}")
            self.is_connected = False
            return False
    
    def get_well_data(self, report_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Получает данные по скважине APS.
        
        ВНИМАНИЕ! Здесь нужно будет заменить запросы на реальные,
        когда будет известна структура таблиц.
        
        Сейчас возвращает тестовые данные для отладки.
        
        Args:
            report_type: тип отчета (не используется в APS, но оставлен для совместимости)
        """
        # TODO: Заменить на реальные SQL-запросы к существующей БД
        # Пример реального запроса (раскомментировать и адаптировать):
        
        if not self.is_connected:
            return self._get_mock_data()
        
        try:
            cursor = self.connection.cursor()
            # Пример запроса - ЗАМЕНИТЕ НА РЕАЛЬНЫЙ!
            cursor.execute("""
                SELECT 
                    well_name as ANNU_NAME,
                    run_number as MWTI_RUN_NO,
                    field_name as OOIN_NAME,
                    pad_name as FCTY_NAME,
                    path as PATH_NAME,
                    use_path as USE_PATH_IN_NAME
                FROM your_aps_table
                WHERE ... 
                ORDER BY ... DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return self._get_mock_data()
            
        except Exception as e:
            logger.error(f"Ошибка получения данных APS: {e}")
            return self._get_mock_data()
        
        
        # Пока возвращаем тестовые данные
        logger.info("APS: Используются тестовые данные (реальная БД не настроена)")
        return self._get_mock_data()
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """
        Возвращает тестовые данные для отладки, пока нет реальной БД
        """
        return {
            'ANNU_NAME': 'APS_TEST_WELL_001',
            'MWTI_RUN_NO': '001',
            'OOIN_NAME': 'APS_FIELD',
            'FCTY_NAME': 'APS_PAD',
            'PATH_NAME': 'APS_Path',
            'USE_PATH_IN_NAME': True
        }
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """
        Выполняет произвольный SQL-запрос к APS БД
        
        Args:
            query: SQL запрос
            params: параметры запроса
            
        Returns:
            Список словарей с результатами или None при ошибке
        """
        if not self.is_connected:
            logger.error("Нет подключения к APS БД")
            return None
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            query_upper = query.strip().upper()
            is_select = query_upper.startswith('SELECT') or 'SELECT ' in query_upper
            
            if is_select:
                # Возвращаем результаты как список словарей
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                return []
            else:
                # Для INSERT/UPDATE/DELETE
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса APS: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_table_list(self) -> Optional[list]:
        """Получает список всех таблиц в БД (для отладки)"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Таблицы в APS БД: {tables}")
            return tables
        except Exception as e:
            logger.error(f"Ошибка получения списка таблиц: {e}")
            return None
    
    def get_table_schema(self, table_name: str) -> Optional[list]:
        """Получает схему таблицы (для отладки)"""
        if not self.is_connected:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            logger.info(f"Схема таблицы {table_name}: {schema}")
            return schema
        except Exception as e:
            logger.error(f"Ошибка получения схемы таблицы: {e}")
            return None
    
    def close_connection(self):
        """Закрывает соединение с БД"""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("Соединение с APS БД закрыто")


# Глобальный экземпляр менеджера APS БД
aps_db_manager = APSDatabaseManager()