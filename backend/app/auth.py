from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from datetime import datetime, timedelta
from jose import jwt
import sqlite3
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import jose

# Load environment variables
load_dotenv()

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
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DATABASE = os.getenv("DATABASE_URL", "backend.db").replace("sqlite:///", "")

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
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            print("Warning: ADMIN_PASSWORD not set in environment variables")
            return
            
        hashed_password = pwd_context.hash(admin_password)
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
            (admin_username, hashed_password)
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
        print(f"Login attempt for username: {login_data.username}")  # Debug log
        
        # Generate token for any provided credentials
        token = jwt.encode({
            "sub": login_data.username,
            "exp": datetime.utcnow() + timedelta(hours=24)  # Extended to 24 hours
        }, SECRET_KEY, algorithm=ALGORITHM)
        
        print(f"Token generated successfully for {login_data.username}")  # Debug log
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": login_data.username
        }
    except Exception as e:
        print(f"Login error: {e}")  # Debug log
        print(f"SECRET_KEY: {SECRET_KEY}")  # Debug log
        print(f"ALGORITHM: {ALGORITHM}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

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
    except jose.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again")
    except jose.exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")
    