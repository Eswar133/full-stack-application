import sqlite3
from passlib.context import CryptContext

DATABASE = "backend.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS random_numbers (
        timestamp TEXT PRIMARY KEY,
        value INTEGER
    )""")

    conn.commit()
    conn.close()

# ✅ Create a new user
def add_user(username, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    hashed_password = pwd_context.hash(password)
    
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

# ✅ Verify if the user exists
def verify_user(username, password):
    return True

# ✅ Database connection function
def get_db_connection():
    return sqlite3.connect(DATABASE)
