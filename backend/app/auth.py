from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from datetime import datetime, timedelta
import jwt
import sqlite3
from passlib.context import CryptContext
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter()
bearer = HTTPBearer()

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secure-secret-key-here"  # Use env var in production
ALGORITHM = "HS256"
DATABASE = "backend.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

# Create initial user (run once)
def create_initial_user():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        hashed_password = pwd_context.hash("admin123")
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
            ("admin", hashed_password)
        )
        conn.commit()
    finally:
        conn.close()

# Initialize database and create initial user
init_db()
create_initial_user()

@router.post("/login")
async def login(login_data: LoginRequest):
    """Accept any username/password combination and return a token."""
    # Generate token for any provided credentials
    token = jwt.encode({
        "sub": login_data.username,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": login_data.username
    }

async def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Verify the JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload["sub"]
        request.state.username = username
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")