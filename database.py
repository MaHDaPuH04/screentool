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
        """Получение данных по скважине включая последние данные из всех таблиц"""
        if not self.is_connected:
            # Возвращаем тестовые данные для демонстрации
            return {
                'ANNU_NAME': 'TEST_WELL_001',
                'BHAR_MWD_RUN_NUM': '001',
                'OOIN_NAME': 'TEST_FIELD',
                'FCTY_NAME': 'TEST_PAD',
                'PATH_NAME': 'TestPath'
            }
            
        try:
            query = """
            SELECT TOP 1
                a.ANNU_NAME,
                b.BHAR_MWD_RUN_NUM,
                o.OOIN_NAME,
                f.FCTY_NAME,
                p.PATH_NAME
            FROM (
                -- Берем последний ANNULUS по времени
                SELECT TOP 1 ANNU_NAME
                FROM dbo.ANNULUS 
                WHERE ANNU_NAME IS NOT NULL 
                ORDER BY ANNU_TIME DESC
            ) a
            CROSS JOIN (
                -- Берем последний BHA_RUN по времени подбора
                SELECT TOP 1 BHAR_MWD_RUN_NUM
                FROM dbo.BHA_RUN 
                WHERE BHAR_MWD_RUN_NUM IS NOT NULL 
                ORDER BY BHAR_PICKUP_TIME DESC
            ) b
            CROSS JOIN (
                -- Берем последний OBJECT_OF_INTEREST_TAB по дате обновления
                SELECT TOP 1 OOIN_NAME
                FROM dbo.OBJECT_OF_INTEREST_TAB 
                WHERE OOIN_NAME IS NOT NULL 
                ORDER BY OOIN_UPDATE_DATE DESC
            ) o
            CROSS JOIN (
                -- Берем последний FACILITY_TAB по дате обновления
                SELECT TOP 1 FCTY_NAME
                FROM dbo.FACILITY_TAB 
                WHERE FCTY_NAME IS NOT NULL 
                ORDER BY FCTY_UPDATE_DATE DESC
            ) f
            CROSS JOIN (
                -- Берем последний PATH по времени создания
                SELECT TOP 1 PATH_NAME
                FROM dbo.PATH 
                WHERE PATH_NAME IS NOT NULL 
                ORDER BY PATH_ST_TIME DESC
            ) p
            """
            
            result = self.execute_query(query)
            
            if result:
                data = result[0]
                logger.info(f"✅ Получены актуальные данные:")
                logger.info(f"   Скважина: {data.get('ANNU_NAME')}")
                logger.info(f"   Рейс: {data.get('BHAR_MWD_RUN_NUM')}")
                logger.info(f"   Месторождение: {data.get('OOIN_NAME')}")
                logger.info(f"   Куст: {data.get('FCTY_NAME')}")
                logger.info(f"   Сайдтрак: {data.get('PATH_NAME')}")
            
            return result[0] if result else None
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных скважины: {e}")
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