"""
Модуль для работы с Microsoft SQL Server
"""
import pyodbc
from logger import logger
from config import config


class DatabaseManager:
    def __init__(self):
        self.connection_string = None
        self.connection = None
        self.is_connected = False
    
    def auto_connect(self):
        """Автоматическое подключение при запуске"""
        try:
            # ИСПОЛЬЗУЕМ НАСТРОЙКИ ИЗ КОНФИГА
            self.connection_string = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={config.db_server};"
                f"DATABASE={config.db_database};"
                f"Trusted_Connection=yes;"
            )
            
            self.connection = pyodbc.connect(self.connection_string)
            self.is_connected = True
            logger.info(f"Автоподключение к БД установлено успешно: {config.db_server}")
            return True
            
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Автоподключение к БД не удалось: {e}")
            return False
    
    def get_well_data(self):
        """Получение самых свежих данных по скважине"""
        if not self.is_connected:
            return None
        
        try:
            query = """
            SELECT TOP 1
                a.ANNU_NAME,
                b.BHAR_MWD_RUN_NUM,
                o.OOIN_NAME,
                f.FCTY_NAME
            FROM (
                SELECT TOP 1 BHAR_MWD_RUN_NUM, WLBR_IDENTIFIER 
                FROM BHA_RUN 
                WHERE BHAR_MWD_RUN_NUM IS NOT NULL
                ORDER BY BHAR_PICKUP_TIME DESC, BHAR_LAYDOWN_TIME DESC
            ) b
            INNER JOIN (
                SELECT TOP 1 ANNU_NAME, WLBR_IDENTIFIER 
                FROM ANNULUS 
                WHERE ANNU_NAME IS NOT NULL
                ORDER BY ANNU_TIME DESC
            ) a ON a.WLBR_IDENTIFIER = b.WLBR_IDENTIFIER
            CROSS JOIN (
                SELECT TOP 1 OOIN_NAME 
                FROM OBJECT_OF_INTEREST_TAB 
                WHERE OOIN_NAME IS NOT NULL AND OOIN_NAME != 'Default Field'
                ORDER BY OOIN_UPDATE_DATE DESC
            ) o
            CROSS JOIN (
                SELECT TOP 1 FCTY_NAME 
                FROM FACILITY_TAB 
                WHERE FCTY_NAME IS NOT NULL AND FCTY_NAME != 'Default Facility'
                ORDER BY FCTY_UPDATE_DATE DESC
            ) f
            """
        
            result = self.execute_query(query)
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Ошибка получения данных скважины: {e}")
            return None
    
    def execute_query(self, query, params=None):
        """Выполняет SQL запрос и возвращает результат"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return None
    
    def close_connection(self):
        """Закрывает соединение с БД"""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("Соединение с БД закрыто")


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()