from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    password = "password123"
    print(f"Hashing '{password}' (len={len(password)})...")
    hashed = pwd_context.hash(password)
    print(f"Hash: {hashed}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
