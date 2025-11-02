import pyodbc

def explore_tables():
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER=TYUMWD212\\ADVANTAGE2017;"
        f"DATABASE=advantage;"
        f"Trusted_Connection=yes;"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("=== СТРУКТУРА ТАБЛИЦ ===")
    
    # 1. Посмотрим какие таблицы есть
    print("\n📋 ТАБЛИЦЫ В БАЗЕ:")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in sorted(tables):
        print(f"   - {table}")
    
    # 2. Структура ключевых таблиц
    key_tables = ['ANNULUS', 'BHA_RUN', 'OBJECT_OF_INTEREST_TAB', 'FACILITY_TAB']
    
    for table in key_tables:
        if table in tables:
            print(f"\n🔍 СТРУКТУРА {table}:")
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """)
            for row in cursor.fetchall():
                print(f"   {row.COLUMN_NAME} ({row.DATA_TYPE}) - nullable: {row.IS_NULLABLE}")
    
    # 3. Посмотрим несколько записей из BHA_RUN
    print(f"\n📊 ДАННЫЕ ИЗ BHA_RUN (первые 5 записей):")
    cursor.execute("SELECT TOP 5 * FROM BHA_RUN")
    columns = [column[0] for column in cursor.description]
    print(f"   Колонки: {columns}")
    
    for row in cursor.fetchall():
        print(f"   {dict(zip(columns, row))}")
    
    conn.close()

if __name__ == "__main__":
    explore_tables()