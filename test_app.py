# test_db_final.py
import pyodbc

def test():
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER=TYUMWD212\\ADVANTAGE2017;"
            f"DATABASE=advantage;"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        print("✅ Тест БД: УСПЕХ")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Тест БД: {e}")
        return False

if __name__ == "__main__":
    test()