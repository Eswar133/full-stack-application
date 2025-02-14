# Backend Documentation

## 🛠️ Full-Stack Application Backend

This backend application is built with FastAPI, SQLite, Pandas, and WebSockets to provide real-time CSV editing and concurrency management.

### 📂 Directory Structure
```
backend/
    ├── app/
        ├── auth.py              # Authentication and token management
        ├── database.py          # SQLite database operations
        ├── file_operations.py   # CSV file management with locking
        ├── main.py              # FastAPI entry point
        ├── routes.py            # API endpoints for CSV CRUD
        ├── websocket.py         # WebSocket and lock management
        ├── backend_table.csv    # CSV data file
        ├── backend.db           # SQLite database file
        └── backups/             # CSV backups
```

### ⚙️ Environment Setup

Ensure Python 3.11+ is installed.

#### 1️⃣ Install Dependencies
```bash
cd backend/app
pip install -r requirements.txt
```

#### 2️⃣ Run the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3️⃣ Access API Docs
- Open: [http://localhost:8000/docs](http://localhost:8000/docs)

### 📋 Core Features

1. **Authentication & Session Management:**
    - Basic Auth login with JWT token generation.
    - Token-based authorization for protected routes.

2. **CSV File Operations:**
    - Read, add, update, and delete CSV entries.
    - Real-time updates broadcast via WebSockets.

3. **Concurrency Control:**
    - Row-level locks to prevent simultaneous edits.
    - Automatic lock expiration after 15 minutes.
    - 15-second cooldown after editing.

4. **Real-Time Data Streaming:**
    - WebSocket streams random numbers every second.
    - CSV updates are immediately pushed to clients.

### 🔑 Authentication

The application uses JWT tokens with a shared secret key.
- Username/Password is accepted without validation.
- Token expiry: 24 hours.

### 🔍 API Endpoints

| Method | Endpoint             | Description                 |
|--------|----------------------|------------------------------|
| POST   | `/api/login`         | Login and get access token    |
| POST   | `/api/register`      | Register a new user           |
| POST   | `/api/logout`        | Log out the current session   |
| GET    | `/api/fetch_csv`     | Fetch CSV data                |
| POST   | `/api/add_csv`       | Add a new CSV entry           |
| PUT    | `/api/update_csv/{index}` | Update a CSV entry       |
| DELETE | `/api/delete_csv/{index}` | Delete a CSV entry       |
| GET    | `/api/numbers`       | Get random numbers            |

### 🌐 WebSocket Events

The backend broadcasts these events to all connected clients:

- **`random_number`**: New random number each second.
- **`csv_update`**: CSV data updated.
- **`lock_status`**: Lock or unlock events for rows.

### 🔍 Edge Cases Handled

1. **Locking Conflicts:**
    - Only one user can edit a row at a time.
2. **Unauthorized Unlocking:**
    - Only the lock owner can unlock a row.
3. **Auto-Release Locks:**
    - Locks expire after 15 minutes.
4. **Cooldown Period:**
    - Rows are locked for 15 seconds after editing.

### 🛠️ Debugging Tips

- **Server not starting?**
  - Check Python environment: `python3 -m venv venv`
  - Install requirements: `pip install -r requirements.txt`

- **CSV file issues?**
  - Ensure the `backend_table.csv` file exists.
  - Run the server; it auto-creates the file if missing.

- **WebSocket not connecting?**
  - Check server logs for errors.
  - Verify frontend uses correct `ws://` URL.

### 🚧 Common Commands
| Command                         | Description                       |
|---------------------------------|-----------------------------------|
| `uvicorn main:app --reload`     | Start server in dev mode          |
| `python database.py`            | Initialize the database           |
| `tail -f app.log`               | Monitor logs (Linux/macOS)         |

### 🔗 External Libraries
- **FastAPI:** Web framework
- **SQLite:** Database
- **Pandas:** CSV file handling
- **websockets:** Real-time communication
- **passlib:** Password hashing
- **PyJWT:** Token handling

### 🚀 Performance Considerations
- **Lock Cleanup:**
  - Runs every 5 seconds.
- **WebSocket Connections:**
  - Broadcasts updates to all clients.

### 📖 Notes
- Avoid modifying `backend_table.csv` manually.
- CSV updates are automatically backed up to the `backups/` directory.



