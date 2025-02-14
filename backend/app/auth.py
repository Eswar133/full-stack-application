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
from typing import Dict, Optional

# Active sessions store
active_sessions: Dict[str, str] = {}  # username -> token mapping

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
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
            password TEXT,
            last_login TIMESTAMP,
            session_token TEXT
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

@router.post("/register")
async def register(register_data: RegisterRequest):
    """Handle user registration"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (register_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password and store new user
        hashed_password = pwd_context.hash(register_data.password)
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (register_data.username, hashed_password)
        )
        conn.commit()
        
        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")
    finally:
        conn.close()

def invalidate_existing_session(username: str):
    """Invalidate any existing session for the user"""
    if username in active_sessions:
        del active_sessions[username]
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET session_token = NULL WHERE username = ?",
        (username,)
    )
    conn.commit()
    conn.close()

@router.post("/login")
async def login(login_data: LoginRequest):
    """Accept any username/password combination and return a token."""
    try:
        # Generate token for any provided credentials
        token = jwt.encode({
            "sub": login_data.username,
            "exp": datetime.utcnow() + timedelta(hours=24)  # Extended to 24 hours
        }, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": login_data.username
        }
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Handle user logout"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload["sub"]
        invalidate_existing_session(username)
        return {"message": "Logged out successfully"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Verify the JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        request.state.username = username
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")
    