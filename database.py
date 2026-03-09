"""
Модуль для работы с Microsoft SQL Server
"""
import pyodbc
import datetime
import concurrent.futures
from typing import Optional
from logger import logger
from config import config


class DatabaseManager:
    def __init__(self):
        self.connection_string = None
        self.connection = None
        self.is_connected = False
        self.current_server = None

    def build_connection_string(self, server: str, timeout: int = None) -> str:
        if timeout is None:
            timeout = config.db_connection_timeout
        return (
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={config.db_database};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout={timeout};"
        )

    def test_connection(self, server: str, timeout: int = None) -> bool:
        try:
            if timeout is None:
                timeout = config.db_connection_timeout
            conn_str = self.build_connection_string(server, timeout)
            conn = pyodbc.connect(conn_str, timeout=timeout, autocommit=True)
            conn.close()
            return True
        except Exception:
            return False

    def get_max_annu_time(self, server: str) -> Optional[datetime.datetime]:
        try:
            conn_str = self.build_connection_string(server, timeout=config.db_connection_timeout)
            conn = pyodbc.connect(conn_str, timeout=config.db_connection_timeout, autocommit=True)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(ANNU_TIME) FROM dbo.ANNULUS")
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return row[0]
            return datetime.datetime(1900, 1, 1)  # сервер доступен, но данных нет
        except Exception:
            return None

    def server_has_data(self, server: str, timeout: int = None) -> bool:
        """
        Быстрая проверка: есть ли хотя бы одна запись в dbo.ANNULUS.
        Возвращает True, если сервер доступен и таблица не пуста.
        """
        try:
            if timeout is None:
                timeout = config.db_connection_timeout
            conn_str = self.build_connection_string(server, timeout)
            conn = pyodbc.connect(conn_str, timeout=timeout, autocommit=True)
            cursor = conn.cursor()
            # Максимально быстрый запрос — проверка существования строки
            cursor.execute("SELECT TOP 1 1 FROM dbo.ANNULUS")
            row = cursor.fetchone()
            conn.close()
            return row is not None
        except Exception as e:
            logger.debug(f"Сервер {server}: ошибка проверки данных — {e}")
            return False

    def select_best_server(self) -> tuple[Optional[str], bool]:
        """
        Параллельная проверка всех серверов.
        Возвращает (имя_сервера, True) — первый сервер, который:
            - доступен по сети
            - содержит данные в таблице ANNULUS.
        Если ни один не подошёл — (None, False).
        """
        logger.info("🔍 Автоматический выбор сервера БД (только проверка наличия данных)...")

        # Если уже есть рабочий сервер в конфиге — проверяем его в первую очередь
        if config.db_server:
            if self.test_connection(config.db_server) and self.server_has_data(config.db_server):
                logger.info(f"✅ Используем ранее выбранный сервер: {config.db_server}")
                return config.db_server, True

        # Параллельная проверка всех серверов из списка
        def check(server):
            if self.test_connection(server, config.db_connection_timeout):
                if self.server_has_data(server, config.db_connection_timeout):
                    return server
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(config.db_servers_to_try)) as executor:
            futures = {executor.submit(check, srv): srv for srv in config.db_servers_to_try}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=config.db_connection_timeout + 0.5)
                    if result:
                        # Отменяем остальные задачи
                        for f in futures:
                            f.cancel()
                        logger.info(f"✅ Выбран сервер: {result} (данные есть)")
                        return result, True
                except Exception:
                    continue

        logger.error("❌ Нет доступных серверов с данными в таблице ANNULUS")
        return None, False

    def auto_connect(self, server: str = None) -> bool:
        """Подключается к указанному серверу и сохраняет его в конфиг."""
        if server is None:
            server = config.db_server
        if not server:
            return False
        try:
            self.connection_string = self.build_connection_string(server)
            self.connection = pyodbc.connect(self.connection_string,
                                            timeout=config.db_connection_timeout,
                                            autocommit=True)
            self.is_connected = True
            self.current_server = server
            config.db_server = server
            config.save_to_file()
            logger.info(f"✅ Подключение к БД: {server}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к {server}: {e}")
            return False
    
    def execute_scalar(self, query: str):
        """Выполняет запрос и возвращает первое значение первой строки или None."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row and row[0] is not None else None
        except Exception as e:
            logger.error(f"Ошибка в execute_scalar: {e}")
            return None
    
    def get_well_data(self):
        """Получение данных по скважине — каждый параметр отдельным запросом, с дефолтными значениями."""
        if not self.is_connected:
            # Офлайн-режим — тестовые данные
            return {
                'ANNU_NAME': 'TEST_WELL_001',
                'MWTI_RUN_NO': '001',
                'OOIN_NAME': 'TEST_FIELD',
                'FCTY_NAME': 'TEST_PAD',
                'PATH_NAME': 'TestPath',
                'USE_PATH_IN_NAME': True
            }

        result = {}

        try:
            # --- Скважина ---
            query_annu = "SELECT TOP 1 ANNU_NAME FROM dbo.ANNULUS ORDER BY ANNU_TIME DESC"
            annu = self.execute_scalar(query_annu)
            result['ANNU_NAME'] = annu if annu else "UNKNOWN_WELL"

            # --- Рейс (Run number) ---
            query_run = """
                SELECT TOP 1 MWTI_RUN_NO 
                FROM dbo.MWD_TIME 
                WHERE MWTI_RUN_NO IS NOT NULL 
                ORDER BY MWTI_TIME DESC
            """
            run = self.execute_scalar(query_run)
            result['MWTI_RUN_NO'] = run if run else "001"

            # --- Месторождение ---
            query_ooin = """
                SELECT TOP 1 OOIN_NAME 
                FROM dbo.OBJECT_OF_INTEREST_TAB 
                WHERE OOIN_NAME IS NOT NULL 
                ORDER BY OOIN_UPDATE_DATE DESC
            """
            ooin = self.execute_scalar(query_ooin)
            result['OOIN_NAME'] = ooin if ooin else "UNKNOWN_FIELD"

            # --- Куст ---
            query_fcty = """
                SELECT TOP 1 FCTY_NAME 
                FROM dbo.FACILITY_TAB 
                WHERE FCTY_NAME IS NOT NULL 
                ORDER BY FCTY_UPDATE_DATE DESC
            """
            fcty = self.execute_scalar(query_fcty)
            result['FCTY_NAME'] = fcty if fcty else "UNKNOWN_PAD"

            # --- Сайдтрак (PATH) ---
            query_path = """
                SELECT TOP 1 PATH_NAME 
                FROM dbo.PATH 
                WHERE PATH_NAME IS NOT NULL 
                ORDER BY PATH_ST_TIME DESC
            """
            path = self.execute_scalar(query_path)
            result['PATH_NAME'] = path if path else ""

            # --- Флаг использования PATH в имени ---
            use_path = True
            if path and "Orig Path" in path:
                use_path = False
            result['USE_PATH_IN_NAME'] = use_path

            # Логирование
            logger.info("✅ Получены данные скважины:")
            logger.info(f"   Скважина: {result['ANNU_NAME']}")
            logger.info(f"   Рейс: {result['MWTI_RUN_NO']}")
            logger.info(f"   Месторождение: {result['OOIN_NAME']}")
            logger.info(f"   Куст: {result['FCTY_NAME']}")
            logger.info(f"   Сайдтрак: {result['PATH_NAME']}")
            logger.info(f"   Использовать PATH в имени: {'ДА' if use_path else 'НЕТ'}")

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных скважины: {e}")
            # При любой ошибке возвращаем тестовые данные с пометкой
            return {
                'ANNU_NAME': 'ERROR_WELL',
                'MWTI_RUN_NO': '001',
                'OOIN_NAME': 'ERROR_FIELD',
                'FCTY_NAME': 'ERROR_PAD',
                'PATH_NAME': '',
                'USE_PATH_IN_NAME': False
            }
    
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