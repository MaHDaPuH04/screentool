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
            return datetime.datetime(1900, 1, 1)
        except Exception:
            return None

    def server_has_data(self, server: str, timeout: int = None) -> bool:
        try:
            if timeout is None:
                timeout = config.db_connection_timeout
            conn_str = self.build_connection_string(server, timeout)
            conn = pyodbc.connect(conn_str, timeout=timeout, autocommit=True)
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 1 FROM dbo.ANNULUS")
            row = cursor.fetchone()
            conn.close()
            return row is not None
        except Exception as e:
            logger.debug(f"Сервер {server}: ошибка проверки данных — {e}")
            return False

    def select_best_server(self) -> tuple[Optional[str], bool]:
        logger.info("🔍 Автоматический выбор сервера БД (только проверка наличия данных)...")

        if config.db_server:
            if self.test_connection(config.db_server) and self.server_has_data(config.db_server):
                logger.info(f"✅ Используем ранее выбранный сервер: {config.db_server}")
                return config.db_server, True

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
                        for f in futures:
                            f.cancel()
                        logger.info(f"✅ Выбран сервер: {result} (данные есть)")
                        return result, True
                except Exception:
                    continue

        logger.error("❌ Нет доступных серверов с данными в таблице ANNULUS")
        return None, False

    def auto_connect(self, server: str = None) -> bool:
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
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                return row[0] if len(row) > 0 else None
            return None
        except Exception as e:
            logger.error(f"Ошибка в execute_scalar: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    def get_well_data(self, report_type=None):
        """
        Получение данных по скважине.
        report_type: ключ (1, 2, 3, 4) или строка ('PreTIP', 'PreRun', 'PostRun', 'Custom')
        """
        # Конвертируем в правильный формат
        report_type_str = None
        
        # Если пришло число
        if isinstance(report_type, int):
            report_type_str = config.report_types.get(report_type, "Custom")
            logger.info(f"get_well_data: получен int {report_type} -> строка '{report_type_str}'")
        # Если пришла строка, но это цифра
        elif isinstance(report_type, str) and report_type.isdigit():
            report_key = int(report_type)
            report_type_str = config.report_types.get(report_key, "Custom")
            logger.info(f"get_well_data: получена строка-цифра '{report_type}' -> int {report_key} -> строка '{report_type_str}'")
        # Если пришла нормальная строка
        elif isinstance(report_type, str):
            report_type_str = report_type
            logger.info(f"get_well_data: получена строка '{report_type_str}'")
        else:
            report_type_str = ""
            logger.info(f"get_well_data: получен неизвестный тип {type(report_type)} = {report_type}")
        
        if not self.is_connected:
            return {
                'ANNU_NAME': 'TEST_WELL_001',
                'MWTI_RUN_NO': 'LAST_RUN' if report_type_str == 'PreTIP' else '001',
                'OOIN_NAME': 'TEST_FIELD',
                'FCTY_NAME': 'TEST_PAD',
                'PATH_NAME': 'TestPath',
                'USE_PATH_IN_NAME': True
            }

        result = {}
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # --- Скважина ---
            cursor.execute("SELECT TOP 1 ANNU_NAME FROM dbo.ANNULUS ORDER BY ANNU_TIME DESC")
            row = cursor.fetchone()
            result['ANNU_NAME'] = row[0] if row and row[0] else "UNKNOWN_WELL"

            # --- Номер рейса - в зависимости от типа отчета ---
            if report_type_str == "PreTIP":
                # PreTIP: последний созданный рейс из MWD_RUN
                logger.info("🔍 PreTIP режим - ищем последний созданный рейс в MWD_RUN")
                cursor.execute("""
                    SELECT TOP 1 MWRU_NUMBER
                    FROM dbo.MWD_RUN
                    WHERE MWRU_NUMBER IS NOT NULL
                    ORDER BY MWRU_DATETIME_START DESC
                """)
                row = cursor.fetchone()
                run = row[0] if row and row[0] else None
                logger.info(f"PreTIP: последний рейс из MWD_RUN = {run}")
            else:
                # PreRun, PostRun, Custom: активный рейс из MWD_TIME
                logger.info(f"🔍 {report_type_str} режим - ищем активный рейс в MWD_TIME")
                cursor.execute("""
                    SELECT TOP 1 MWTI_RUN_NO
                    FROM dbo.MWD_TIME
                    WHERE MWTI_RUN_NO IS NOT NULL
                    ORDER BY MWTI_TIME DESC
                """)
                row = cursor.fetchone()
                run = row[0] if row and row[0] else None
                logger.info(f"Активный рейс из MWD_TIME = {run}")

            result['MWTI_RUN_NO'] = str(run) if run is not None else "001"

                # --- Остальные данные ---
            cursor.execute("""
                SELECT TOP 1 OOIN_NAME
                FROM dbo.OBJECT_OF_INTEREST_TAB
                WHERE OOIN_NAME IS NOT NULL
                ORDER BY OOIN_UPDATE_DATE DESC
            """)
            row = cursor.fetchone()
            result['OOIN_NAME'] = row[0] if row and row[0] else "UNKNOWN_FIELD"

            cursor.execute("""
                SELECT TOP 1 FCTY_NAME
                FROM dbo.FACILITY_TAB
                WHERE FCTY_NAME IS NOT NULL
                ORDER BY FCTY_UPDATE_DATE DESC
            """)
            row = cursor.fetchone()
            result['FCTY_NAME'] = row[0] if row and row[0] else "UNKNOWN_PAD"

            cursor.execute("""
                SELECT TOP 1 PATH_NAME
                FROM dbo.PATH
                WHERE PATH_NAME IS NOT NULL
                ORDER BY PATH_ST_TIME DESC
            """)
            row = cursor.fetchone()
            path = row[0] if row and row[0] else ""
            result['PATH_NAME'] = path

            use_path = True
            if path and "Orig Path" in path:
                use_path = False
            result['USE_PATH_IN_NAME'] = use_path

            logger.info(f"✅ Итоговые данные: ANNU_NAME={result['ANNU_NAME']}, MWTI_RUN_NO={result['MWTI_RUN_NO']}, report_type={report_type_str}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных скважины: {e}")
            import traceback
            traceback.print_exc()
            return {
                'ANNU_NAME': 'ERROR_WELL',
                'MWTI_RUN_NO': '001',
                'OOIN_NAME': 'ERROR_FIELD',
                'FCTY_NAME': 'ERROR_PAD',
                'PATH_NAME': '',
                'USE_PATH_IN_NAME': False
            }
        finally:
            if cursor:
                cursor.close()
    
    def execute_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            query_upper = query.strip().upper()
            is_select_query = (
                query_upper.startswith('SELECT') or 
                query_upper.startswith('WITH') or
                ' SELECT ' in query_upper
            )
            
            if is_select_query:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                return []
            else:
                self.connection.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("Соединение с БД закрыто")

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()