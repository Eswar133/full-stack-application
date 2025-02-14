# Backend Documentation

## Overview
The backend is built using FastAPI, providing a robust REST API and WebSocket functionality for real-time data synchronization. The system handles user authentication, data management, and real-time updates through WebSocket connections.

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # Application entry point
│   ├── auth.py           # Authentication logic
│   ├── websocket.py      # WebSocket handling
│   ├── routes.py         # API routes
│   ├── file_operations.py # CSV file operations
│   ├── database.py       # Database operations
│   
│   
├── requirements.txt
└── README.md
```

## Core Components

### 1. Main Application (`main.py`)
```python
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Features:
- FastAPI application initialization
- CORS middleware setup
- WebSocket endpoint registration
- Background task for random number generation
- Database initialization

### 2. Authentication System (`auth.py`)
```python
# JWT Configuration
SECRET_KEY = "your-secure-secret-key-here"
ALGORITHM = "HS256"

# Authentication endpoints
@router.post("/login")
async def login(login_data: LoginRequest)

@router.post("/register")
async def register(register_data: RegisterRequest)

@router.post("/logout")
async def logout(request: Request)
```
Features:
- JWT token generation and validation
- User registration and login
- Session management
- Password hashing with bcrypt
- Token-based authentication

### 3. WebSocket Handler (`websocket.py`)
```python
# Constants
COOLDOWN_SECONDS = 15
EDIT_TIMEOUT_MINUTES = 15

# Connection Management
active_connections: Dict[str, WebSocket] = {}
row_locks: Dict[int, dict] = {}
```
Features:
- Real-time connection management
- Row locking mechanism
- Connection state tracking
- Broadcast messaging
- Ping/Pong health checks

### 4. File Operations (`file_operations.py`)
```python
# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "backend_table.csv")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
```
Features:
- CSV file CRUD operations
- Automatic backup creation
- Data validation
- File locking mechanism
- Error handling

## API Endpoints

### Authentication
```
POST /api/register
- Register new user
- Body: { "username": string, "password": string }

POST /api/login
- Authenticate user
- Body: { "username": string, "password": string }
- Returns: { "access_token": string, "token_type": string }

POST /api/logout
- Logout user
- Requires: Bearer token
```

### Data Management
```
GET /api/fetch_csv
- Fetch all CSV data
- Requires: Bearer token
- Returns: Array of CSV entries

POST /api/add_csv
- Add new CSV entry
- Requires: Bearer token
- Body: CSVEntry model

PUT /api/update_csv/{index}
- Update existing entry
- Requires: Bearer token
- Body: CSVEntry model

DELETE /api/delete_csv/{index}
- Delete CSV entry
- Requires: Bearer token
```

### WebSocket
```
WS /api/ws
- Real-time connection
- Query params: username
- Messages:
  - lock_status
  - csv_update
  - random_number
  - ping
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    last_login TIMESTAMP,
    session_token TEXT
)
```

### Random Numbers Table
```sql
CREATE TABLE random_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    value REAL
)
```

## Data Models

### CSVEntry Model
```python
class CSVEntry(BaseModel):
    user: Optional[str] = Field(default="")
    broker: Optional[str] = Field(default="")
    API_key: Optional[str] = Field(default="")
    API_secret: Optional[str] = Field(default="")
    pnl: Optional[float] = Field(default=0.0)
    margin: Optional[float] = Field(default=0.0)
    max_risk: Optional[float] = Field(default=0.0)
```

## Security Features

### Authentication
- JWT token-based authentication
- Password hashing using bcrypt
- Session management
- Token expiration

### Data Protection
- Row-level locking
- File locking for CSV operations
- Automatic backups
- Input validation

### Connection Security
- WebSocket connection validation
- CORS protection
- Error handling
- Rate limiting

## Error Handling

### HTTP Errors
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 409: Conflict (Row Lock)
- 500: Internal Server Error

### WebSocket Errors
- Connection errors
- Message parsing errors
- Lock acquisition failures
- Broadcast failures

## Setup and Installation

### Prerequisites
```
Python 3.7+
pip
SQLite3
```

### Installation Steps
1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Initialize database:
```bash
python -m app.main
```

### Running the Server
Development:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Performance Considerations

### WebSocket Optimization
- Connection pooling
- Message queuing
- Periodic cleanup
- Connection health monitoring

### Database Optimization
- Connection pooling
- Query optimization
- Index usage
- Transaction management

### File Operations
- File locking
- Backup management
- Error recovery
- Data validation

## Monitoring and Logging

### Application Logs
- Connection events
- Error tracking
- User actions
- Performance metrics

### WebSocket Logs
- Connection status
- Message delivery
- Lock operations
- Broadcast events

## Testing

### Unit Tests
- Route testing
- Authentication testing
- Data validation
- Error handling

### Integration Tests
- API endpoints
- WebSocket functionality
- Database operations
- File operations

### Load Testing
- Connection limits
- Concurrent users
- Message broadcasting
- Lock management 