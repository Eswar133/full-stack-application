# Full-Stack Application Documentation

## 🛠️ Overview

This project is a full-stack web application with a React frontend and a FastAPI backend. It supports real-time CSV data management, user authentication, and live WebSocket streaming.

---

## 🖥️ Tech Stack

- **Frontend:** React, Axios, Chart.js
- **Backend:** FastAPI, SQLite, Pandas, WebSockets
- **Communication:** WebSockets for real-time updates

---

## 📂 Directory Structure

```
full-stack-application/
    ├── backend/
    │    └── app/
    │        ├── auth.py              # Authentication and token management
    │        ├── database.py          # SQLite database operations
    │        ├── file_operations.py   # CSV file management with locking
    │        ├── main.py              # FastAPI entry point
    │        ├── routes.py            # API endpoints for CSV CRUD
    │        ├── websocket.py         # WebSocket and lock management
    │        ├── backend_table.csv    # CSV data file
    │        ├── backend.db           # SQLite database file
    │        └── backups/             # CSV backups
    │
    └── frontend/
         ├── src/
         │   ├── App.js              # Main application component
         │   ├── Dashboard.js        # CSV dashboard component
         │   ├── api.js              # API interactions with the backend
         │   ├── AuthContext.js      # Authentication context
         │   └── index.js            # React entry point
         ├── public/                 # Static assets
         ├── package.json            # Node.js dependencies
         └── README.md               # Frontend documentation
```

---

## 🚀 Running the Application

Follow these steps to run the application with the frontend and backend running in separate terminals.

### 🔧 Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **npm/yarn**

### 📦 Install Dependencies

Open two terminal windows:

1️⃣ **Backend**
```bash
cd backend/app
pip install -r requirements.txt
```

2️⃣ **Frontend**
```bash
cd frontend
npm install
```

### 🏃 Run the Application

1️⃣ **Start Backend**
```bash
cd backend/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2️⃣ **Start Frontend**
```bash
cd frontend
npm start
```

**Important:** Run both commands simultaneously in different terminal windows.

---

## 🔍 Application Features

### 🔑 Authentication
- **Login:** Basic Auth with JWT tokens
- **Token Expiry:** 24 hours
- **Single Session:** Prevents multiple logins with the same credentials.

### 🗂️ CSV File Operations
- **Read:** View CSV data.
- **Add:** Insert new rows.
- **Update:** Modify existing rows.
- **Delete:** Remove rows.
- **Automatic Backups:** Stored in the `backups/` folder.

### 🔒 Concurrency Control
- Row-level locks to prevent simultaneous edits.
- Locks expire after 15 minutes of inactivity.
- Cooldown period of 15 seconds after editing.

### 📡 Real-Time Updates
- New random numbers streamed every second.
- CSV changes broadcasted to all connected clients.

---

## 🌐 API Endpoints

| Method | Endpoint                  | Description                  |
|--------|---------------------------|-------------------------------|
| POST   | `/api/login`               | Authenticate and get token    |
| POST   | `/api/register`            | Register a new user           |
| POST   | `/api/logout`              | Log out current session       |
| GET    | `/api/fetch_csv`           | Fetch CSV data                |
| POST   | `/api/add_csv`             | Add a new CSV entry           |
| PUT    | `/api/update_csv/{index}`  | Update a CSV entry            |
| DELETE | `/api/delete_csv/{index}`  | Delete a CSV entry            |
| GET    | `/api/numbers`             | Fetch random numbers          |
| WS     | `/api/ws`                  | WebSocket connection          |

---

## 🔔 WebSocket Events

| Event Type   | Description                                    |
|--------------|------------------------------------------------|
| `random_number` | Streams random numbers every second        |
| `csv_update`    | Broadcasts CSV changes in real-time        |
| `lock_status`   | Updates clients on row lock/unlock events  |

---

## ⚠️ Edge Cases Handled

1. **Locking Conflicts:** Only one user can edit a row at a time.
2. **Unauthorized Unlocking:** Only the lock owner can release the lock.
3. **Auto-Release Locks:** Locks expire after 15 minutes.
4. **Cooldown Period:** Rows remain locked for 15 seconds after editing.
5. **Invalid Input Handling:** Non-numeric entries default to `0`.

---

## 🧪 Testing the Application

1️⃣ **Access the Frontend:**
- Open: [http://localhost:3000](http://localhost:3000)

2️⃣ **Access the Backend API Docs:**
- Open: [http://localhost:8000/docs](http://localhost:8000/docs)

3️⃣ **Test Real-Time Updates:**
- Open the app in multiple browser tabs.
- Make CRUD operations and observe real-time sync.

---

## 🛠️ Troubleshooting

| Issue                        | Solution                                      |
|-------------------------------|-----------------------------------------------|
| Frontend not loading?         | Check React logs with `npm start`              |
| Backend not responding?       | Restart with `uvicorn main:app --reload`      |
| CSV not updating in UI?       | Refresh the browser or check WebSocket logs   |
| WebSocket disconnects often?  | Check server and network settings             |



## 🌟 Best Practices

- **Secure Environment:** Use environment variables for secrets.
- **Monitor Logs:** Always check logs if real-time updates fail.
- **Handle Concurrency:** WebSocket locks prevent data corruption.

**Happy coding! 🎯**

