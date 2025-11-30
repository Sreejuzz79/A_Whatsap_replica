import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="whatsap"
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    print("Tables in 'whatsap' database:")
    for table in cursor:
        print(table)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
