import json
import sqlite3
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from datetime import datetime, timedelta

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Store row locks: {row_index: (username, timestamp)}
row_locks: Dict[int, tuple] = {}

# Lock timeout in seconds
LOCK_TIMEOUT = 300  # 5 minutes

def is_row_locked(row_index: int, requesting_user: str) -> bool:
    """Check if a row is locked by another user."""
    if row_index not in row_locks:
        return False
    
    username, timestamp = row_locks[row_index]
    if username == requesting_user:
        return False
    
    # Check if lock has expired
    if datetime.now() - timestamp > timedelta(seconds=LOCK_TIMEOUT):
        del row_locks[row_index]
        return False
    
    return True

def get_lock_info(row_index: int) -> dict:
    """Get information about a row lock."""
    if row_index not in row_locks:
        return {"locked": False}
    
    username, timestamp = row_locks[row_index]
    if datetime.now() - timestamp > timedelta(seconds=LOCK_TIMEOUT):
        del row_locks[row_index]
        return {"locked": False}
    
    return {
        "locked": True,
        "locked_by": username,
        "locked_at": timestamp.isoformat()
    }

async def connect_client(websocket: WebSocket, username: str):
    """Connect a new client."""
    await websocket.accept()
    active_connections[username] = websocket

async def disconnect_client(username: str):
    """Disconnect a client and clean up their locks."""
    if username in active_connections:
        # Remove all locks held by this user
        global row_locks
        row_locks = {
            index: (user, timestamp) 
            for index, (user, timestamp) in row_locks.items() 
            if user != username
        }
        del active_connections[username]

async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients."""
    disconnected_users = []
    for username, connection in active_connections.items():
        try:
            await connection.send_json(message)
        except:
            disconnected_users.append(username)
    
    # Clean up disconnected users
    for username in disconnected_users:
        await disconnect_client(username)

async def broadcast_table_update(data: list):
    """Broadcast table update to all connected clients."""
    await broadcast_message({
        "type": "csv_update",
        "data": data
    })

async def broadcast_random_number(value: float, timestamp: str):
    """Broadcast a random number to all connected clients."""
    await broadcast_message({
        "type": "random_number",
        "value": value,
        "timestamp": timestamp
    })

async def handle_lock_request(username: str, row_index: int):
    """Handle a request to lock a row."""
    if is_row_locked(row_index, username):
        return False
    
    row_locks[row_index] = (username, datetime.now())
    await broadcast_message({
        "type": "lock_status",
        "row_index": row_index,
        "locked_by": username
    })
    return True

async def handle_unlock_request(username: str, row_index: int):
    """Handle a request to unlock a row."""
    if row_index in row_locks and row_locks[row_index][0] == username:
        del row_locks[row_index]
        await broadcast_message({
            "type": "lock_status",
            "row_index": row_index,
            "locked_by": None
        })
        return True
    return False

async def send_ping(websocket: WebSocket):
    """Send periodic ping messages to keep the connection alive."""
    while True:
        try:
            await asyncio.sleep(10)
            await websocket.send_json({"type": "ping"})
        except:
            break

async def process_messages(websocket: WebSocket, username: str):
    """Process incoming WebSocket messages."""
    while True:
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "lock_row":
                row_index = message["row_index"]
                success = await handle_lock_request(username, row_index)
                # Send confirmation back to requester
                await websocket.send_json({
                    "type": "lock_confirmation",
                    "row_index": row_index,
                    "success": success
                })
            
            elif message["type"] == "unlock_row":
                row_index = message["row_index"]
                await handle_unlock_request(username, row_index)

        except WebSocketDisconnect:
            break
        except json.JSONDecodeError:
            print(f"Invalid JSON received from {username}")
            continue
        except Exception as e:
            print(f"Error processing message from {username}: {e}")
            continue

async def websocket_endpoint(websocket: WebSocket, username: str):
    """Manage WebSocket connections with user information."""
    if not username or username.lower() == "null":
        await websocket.close(code=4001, reason="Username required")
        return
        
    try:
        # Accept connection and store it
        await websocket.accept()
        active_connections[username] = websocket
        print(f"WebSocket connected for user: {username}")
        
        # Send initial random number
        conn = sqlite3.connect("backend.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM random_numbers ORDER BY timestamp DESC LIMIT 1")
        data = cursor.fetchone()
        conn.close()

        if data:
            await websocket.send_json({
                "type": "random_number",
                "timestamp": data[0],
                "value": data[1]
            })

        # Start both ping and message processing tasks
        await asyncio.gather(
            send_ping(websocket),
            process_messages(websocket, username),
            return_exceptions=True
        )

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {username}")
    except Exception as e:
        print(f"WebSocket error for user {username}: {e}")
    finally:
        # Clean up locks held by disconnected user
        if username in active_connections:
            del active_connections[username]
            
        for row_index in list(row_locks.keys()):
            if row_locks[row_index][0] == username:
                del row_locks[row_index]
                try:
                    await broadcast_message({
                        "type": "lock_status",
                        "row_index": row_index,
                        "locked_by": None
                    })
                except Exception as e:
                    print(f"Error broadcasting lock release: {e}")

async def handle_unlock_request(username: str, row_index: int):
    print(f"Unlock attempt by {username} on row {row_index}")
    # ... existing code