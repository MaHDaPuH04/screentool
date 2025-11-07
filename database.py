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
        """Получение данных по скважине с временной логикой PATH"""
        if not self.is_connected:
            # Возвращаем тестовые данные для демонстрации
            return {
                'ANNU_NAME': 'TEST_WELL_001',
                'MWTI_RUN_NO': '001',
                'OOIN_NAME': 'TEST_FIELD',
                'FCTY_NAME': 'TEST_PAD',
                'PATH_NAME': 'TestPath',
                'USE_PATH_IN_NAME': True
            }
            
        try:
            query = """
            WITH LatestRun AS (
                -- Берем последний MWTI_RUN_NO из MWD_TIME
                SELECT TOP 1 MWTI_RUN_NO, MWTI_TIME
                FROM dbo.MWD_TIME 
                WHERE MWTI_RUN_NO IS NOT NULL 
                ORDER BY MWTI_TIME DESC
            ),
            RunInfo AS (
                -- Информация о текущем рейсе из MWD_RUN
                SELECT TOP 1 MWRU_DATETIME_START
                FROM dbo.MWD_RUN 
                WHERE MWRU_NUMBER = (SELECT MWTI_RUN_NO FROM LatestRun)
                ORDER BY MWRU_DATETIME_START DESC
            ),
            PathInfo AS (
                -- Последний PATH
                SELECT TOP 1 PATH_NAME, PATH_ST_TIME
                FROM dbo.PATH 
                WHERE PATH_NAME IS NOT NULL 
                ORDER BY PATH_ST_TIME DESC
            )
            SELECT 
                a.ANNU_NAME,
                lr.MWTI_RUN_NO,
                o.OOIN_NAME,
                f.FCTY_NAME,
                p.PATH_NAME,
                p.PATH_ST_TIME,
                r.MWRU_DATETIME_START,
                DATEDIFF(MINUTE, p.PATH_ST_TIME, r.MWRU_DATETIME_START) as TIME_DIFF_MINUTES,  -- Изменил порядок!
                CASE 
                    WHEN p.PATH_ST_TIME IS NOT NULL 
                        AND r.MWRU_DATETIME_START IS NOT NULL
                        AND p.PATH_ST_TIME < r.MWRU_DATETIME_START  -- PATH создан ДО рейса
                        AND DATEDIFF(MINUTE, p.PATH_ST_TIME, r.MWRU_DATETIME_START) BETWEEN 1 AND 720  -- Разница от 1 мин до 12 часов
                    THEN 1
                    ELSE 0
                END AS USE_PATH_IN_NAME
            FROM (
                SELECT TOP 1 ANNU_NAME
                FROM dbo.ANNULUS 
                WHERE ANNU_NAME IS NOT NULL 
                ORDER BY ANNU_TIME DESC
            ) a
            CROSS JOIN LatestRun lr
            CROSS JOIN RunInfo r
            CROSS JOIN PathInfo p
            CROSS JOIN (
                SELECT TOP 1 OOIN_NAME
                FROM dbo.OBJECT_OF_INTEREST_TAB 
                WHERE OOIN_NAME IS NOT NULL 
                ORDER BY OOIN_UPDATE_DATE DESC
            ) o
            CROSS JOIN (
                SELECT TOP 1 FCTY_NAME
                FROM dbo.FACILITY_TAB 
                WHERE FCTY_NAME IS NOT NULL 
                ORDER BY FCTY_UPDATE_DATE DESC
            ) f
            """
            
            result = self.execute_query(query)
            
            if result and isinstance(result, list) and len(result) > 0:
                data = result[0]
                
                # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: не используем PATH если содержит "Orig Path"
                path_name = data.get('PATH_NAME', '')
                if path_name and "Orig Path" in path_name:
                    data['USE_PATH_IN_NAME'] = 0
                    logger.info(f"🚫 PATH содержит 'Orig Path' - не используем в имени")
                
                use_path = bool(data.get('USE_PATH_IN_NAME', 0))
                
                # ОТЛАДОЧНАЯ ИНФОРМАЦИЯ
                logger.info(f"✅ Получены актуальные данные:")
                logger.info(f"   Скважина: {data.get('ANNU_NAME')}")
                logger.info(f"   Рейс: {data.get('MWTI_RUN_NO')}")
                logger.info(f"   Месторождение: {data.get('OOIN_NAME')}")
                logger.info(f"   Куст: {data.get('FCTY_NAME')}")
                logger.info(f"   Сайдтрак: {data.get('PATH_NAME')}")
                logger.info(f"   PATH_ST_TIME: {data.get('PATH_ST_TIME')}")
                logger.info(f"   MWRU_DATETIME_START: {data.get('MWRU_DATETIME_START')}")
                logger.info(f"   TIME_DIFF_MINUTES: {data.get('TIME_DIFF_MINUTES')}")
                logger.info(f"   Использовать PATH в имени: {'ДА' if use_path else 'НЕТ'}")
            
                return data
            else:
                return self._try_simple_query()
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных скважины: {e}")
            return self._try_simple_query()

    def _try_simple_query(self):
        """Пробует выполнить упрощенный запрос"""
        try:
            logger.info("Пробуем упрощенный запрос...")
            simple_query = """
            SELECT 
                (SELECT TOP 1 ANNU_NAME FROM dbo.ANNULUS WHERE ANNU_NAME IS NOT NULL ORDER BY ANNU_TIME DESC) as ANNU_NAME,
                (SELECT TOP 1 MWTI_RUN_NO FROM dbo.MWD_TIME WHERE MWTI_RUN_NO IS NOT NULL ORDER BY MWTI_TIME DESC) as MWTI_RUN_NO,
                (SELECT TOP 1 OOIN_NAME FROM dbo.OBJECT_OF_INTEREST_TAB WHERE OOIN_NAME IS NOT NULL ORDER BY OOIN_UPDATE_DATE DESC) as OOIN_NAME,
                (SELECT TOP 1 FCTY_NAME FROM dbo.FACILITY_TAB WHERE FCTY_NAME IS NOT NULL ORDER BY FCTY_UPDATE_DATE DESC) as FCTY_NAME,
                (SELECT TOP 1 PATH_NAME FROM dbo.PATH WHERE PATH_NAME IS NOT NULL ORDER BY PATH_ST_TIME DESC) as PATH_NAME,
                1 as USE_PATH_IN_NAME
            """
            
            result = self.execute_query(simple_query)
            
            if result and isinstance(result, list) and len(result) > 0:
                data = result[0]
                logger.info(f"✅ Получены данные упрощенным запросом:")
                logger.info(f"   Скважина: {data.get('ANNU_NAME')}")
                logger.info(f"   Рейс: {data.get('MWTI_RUN_NO')}")
                logger.info(f"   Месторождение: {data.get('OOIN_NAME')}")
                logger.info(f"   Куст: {data.get('FCTY_NAME')}")
                logger.info(f"   Сайдтрак: {data.get('PATH_NAME')}")
                return data
                
        except Exception as e:
            logger.error(f"❌ Упрощенный запрос тоже не работает: {e}")
        
        return None
    
    def execute_query(self, query, params=None):
        """Выполняет SQL запрос и возвращает результат"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # УЛУЧШЕННАЯ ПРОВЕРКА - смотрим на первые ключевые слова запроса
            query_upper = query.strip().upper()
            is_select_query = (
                query_upper.startswith('SELECT') or 
                query_upper.startswith('WITH') or
                ' SELECT ' in query_upper
            )
            
            if is_select_query:
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results  # Возвращаем список для SELECT/WITH запросов
            else:
                self.connection.commit()
                return cursor.rowcount  # Возвращаем int для INSERT/UPDATE/DELETE
                
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