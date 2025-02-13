from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPAuthorizationCredentials, HTTPBearer
import jwt
import datetime
from passlib.context import CryptContext
from database import verify_user  # ✅ Import verification function
from pydantic import BaseModel

# ✅ Define `router`
router = APIRouter()
security = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"

# ✅ Function to create JWT token
def create_token(username: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    token = jwt.encode({"sub": username, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    return token

# ✅ Verify JWT token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
class LoginData(BaseModel):
    username: str
    password: str

router = APIRouter()

# ✅ Login Route - Use Pydantic model to validate request body
@router.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    token = create_token(credentials.username)
    return {"token": token}