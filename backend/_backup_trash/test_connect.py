import mysql.connector

try:
    print("Connecting...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    print("Connected.")
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    for db in cursor:
        print(db)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
