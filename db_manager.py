import mysql.connector
from mysql.connector import Error
import hashlib

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password=''):
        self.host = host
        self.user = user
        self.password = password
        self.database = 'whatsapp_clone_db'
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_database()
        self.create_tables()
        self.update_schema()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("Connected to MySQL server")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None
            self.cursor = None

    def create_database(self):
        if not self.cursor:
            print("Database connection not established. Cannot create database.")
            return

        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            self.cursor.execute(f"USE {self.database}")
            print(f"Database {self.database} selected")
        except Error as e:
            print(f"Error creating/selecting database: {e}")

    def create_tables(self):
        if not self.cursor:
            return

        try:
            # Users table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Messages table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id)
                )
            """)

            # Contacts table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    user_id INT NOT NULL,
                    contact_id INT NOT NULL,
                    PRIMARY KEY (user_id, contact_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (contact_id) REFERENCES users(id)
                )
            """)
            self.connection.commit()
            print("Tables created successfully")
        except Error as e:
            print(f"Error creating tables: {e}")

    def update_schema(self):
        # Add profile columns if they don't exist
        columns = [
            ("full_name", "VARCHAR(100)"),
            ("mobile_number", "VARCHAR(20)"),
            ("profile_picture", "TEXT"), # Base64 string or path
            ("about", "VARCHAR(255) DEFAULT 'Hey there! I am using WhatsApp Clone.'")
        ]
        
        for col_name, col_type in columns:
            try:
                self.cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name}")
            except Error as e:
                # Ignore if column already exists (Error 1060)
                if e.errno != 1060:
                    print(f"Error adding column {col_name}: {e}")
        self.connection.commit()

    def register_user(self, username, password):
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
            self.cursor.execute(query, (username, password_hash))
            self.connection.commit()
            return True, "User registered successfully"
        except mysql.connector.IntegrityError:
            return False, "Username already exists"
        except Error as e:
            return False, f"Error: {e}"

    def login_user(self, username, password):
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
            self.cursor.execute(query, (username, password_hash))
            user = self.cursor.fetchone()
            if user:
                return True, user
            else:
                return False, "Invalid username or password"
        except Error as e:
            return False, f"Error: {e}"

    def save_message(self, sender_id, receiver_id, content):
        try:
            query = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)"
            self.cursor.execute(query, (sender_id, receiver_id, content))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error saving message: {e}")
            return False

    def get_chat_history(self, user1_id, user2_id):
        try:
            query = """
                SELECT m.*, u.username as sender_name 
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE (sender_id = %s AND receiver_id = %s) 
                   OR (sender_id = %s AND receiver_id = %s)
                ORDER BY timestamp ASC
            """
            self.cursor.execute(query, (user1_id, user2_id, user2_id, user1_id))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching history: {e}")
            return []

    def search_user(self, username):
        try:
            query = "SELECT id, username, full_name, about, profile_picture FROM users WHERE username = %s"
            self.cursor.execute(query, (username,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error searching user: {e}")
            return None

    def add_contact(self, user_id, contact_username):
        try:
            # First find the user
            contact = self.search_user(contact_username)
            if not contact:
                return False, "User not found"
            
            contact_id = contact['id']
            if user_id == contact_id:
                return False, "Cannot add yourself"

            # Check if already exists
            check_query = "SELECT * FROM contacts WHERE user_id = %s AND contact_id = %s"
            self.cursor.execute(check_query, (user_id, contact_id))
            if self.cursor.fetchone():
                return False, "User already in contacts"

            # Add to contacts
            query = "INSERT INTO contacts (user_id, contact_id) VALUES (%s, %s)"
            self.cursor.execute(query, (user_id, contact_id))
            self.connection.commit()
            return True, "Contact added successfully"
        except Error as e:
            return False, f"Error adding contact: {e}"

    def get_contacts(self, user_id):
        try:
            query = """
                SELECT u.id, u.username, u.full_name, u.profile_picture, u.about
                FROM users u
                JOIN contacts c ON u.id = c.contact_id
                WHERE c.user_id = %s
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching contacts: {e}")
            return []

    def update_profile(self, user_id, full_name, mobile_number, about, profile_picture=None):
        try:
            if profile_picture:
                query = "UPDATE users SET full_name=%s, mobile_number=%s, about=%s, profile_picture=%s WHERE id=%s"
                params = (full_name, mobile_number, about, profile_picture, user_id)
            else:
                query = "UPDATE users SET full_name=%s, mobile_number=%s, about=%s WHERE id=%s"
                params = (full_name, mobile_number, about, user_id)
            
            self.cursor.execute(query, params)
            self.connection.commit()
            return True, "Profile updated successfully"
        except Error as e:
            return False, f"Error updating profile: {e}"

    def get_profile(self, user_id):
        try:
            query = "SELECT id, username, full_name, mobile_number, about, profile_picture FROM users WHERE id = %s"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching profile: {e}")
            return None

if __name__ == "__main__":
    db = DatabaseManager()
