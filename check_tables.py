import pyodbc

def check_mwd_structure():
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER=TyuMWD212\\ADVANTAGE2017;"
        f"DATABASE=advantage;"
        f"Trusted_Connection=yes;"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("=== СТРУКТУРА MWD_RUN ===")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'MWD_RUN'
        ORDER BY ORDINAL_POSITION
    """)
    for row in cursor.fetchall():
        print(f"   {row.COLUMN_NAME} ({row.DATA_TYPE}) - nullable: {row.IS_NULLABLE}")
    
    print("\n=== СТРУКТУРА MWD_TIME ===")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'MWD_TIME'
        ORDER BY ORDINAL_POSITION
    """)
    for row in cursor.fetchall():
        print(f"   {row.COLUMN_NAME} ({row.DATA_TYPE}) - nullable: {row.IS_NULLABLE}")
    
    print("\n=== ПЕРВЫЕ ЗАПИСИ MWD_RUN ===")
    cursor.execute("SELECT TOP 3 * FROM MWD_RUN")
    columns = [column[0] for column in cursor.description]
    print(f"Колонки: {columns}")
    for row in cursor.fetchall():
        print(dict(zip(columns, row)))
    
    print("\n=== ПЕРВЫЕ ЗАПИСИ MWD_TIME ===")
    cursor.execute("SELECT TOP 3 * FROM MWD_TIME ORDER BY MWTI_TIME DESC")
    columns = [column[0] for column in cursor.description]
    print(f"Колонки: {columns}")
    for row in cursor.fetchall():
        print(dict(zip(columns, row)))
    
    conn.close()

if __name__ == "__main__":
    check_mwd_structure()