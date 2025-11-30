from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

try:
    password = "password123"
    print(f"Hashing '{password}'...")
    hashed = pwd_context.hash(password)
    print(f"Hash: {hashed}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
