import mysql.connector
import sys

print("Starting script...")
try:
    print("Connecting to server...")
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    print("Connected to server.")
    cursor = conn.cursor()
    
    print("Listing databases:")
    cursor.execute("SHOW DATABASES")
    for db in cursor:
        print(db)
        
    print("Switching to 'whatsap'...")
    cursor.execute("USE whatsap")
    print("Switched to 'whatsap'.")
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS call_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        caller_id INT NOT NULL,
        receiver_id INT NOT NULL,
        status VARCHAR(20) NOT NULL,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    print("Executing query...")
    cursor.execute(create_table_query)
    print("Table 'call_logs' created successfully (or already exists).")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
