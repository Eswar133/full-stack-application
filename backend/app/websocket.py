import json
import sqlite3
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from datetime import datetime, timedelta

# Constants for lock timeouts
EDIT_TIMEOUT_MINUTES = 15  # Maximum time a user can hold a lock
COOLDOWN_SECONDS = 15      # Cooldown period after editing (in seconds)

active_connections: Dict[str, WebSocket] = {}
row_locks: Dict[int, dict] = {}  # Stores {row_index: {username, expires_at, status, last_modified}}


def is_row_locked(row_index: int, requesting_user: str) -> bool:
    if row_index not in row_locks:
        return False
    
    lock = row_locks[row_index]
    now = datetime.now()
    
    # If lock has expired, clean it up
    if now > lock['expires_at']:
        del row_locks[row_index]
        return False
    
    # Check cooldown period
    if lock['status'] == 'cooldown':
        if now > lock['expires_at']:
            del row_locks[row_index]
            return False
        return True  # Still in cooldown
    
    # If the requesting user has the lock and it's in editing state, allow them to continue
    if lock['status'] == 'editing' and lock['username'] == requesting_user:
        # Update expiration time if they're still actively editing
        lock['expires_at'] = now + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
        return False
    
    # For all other cases (different user or cooldown period), the row is locked
    return True


async def validate_and_clean_locks():
    """Periodically validate locks and clean up expired ones"""
    now = datetime.now()
    expired_locks = []
    
    for row_index, lock in row_locks.items():
        if now > lock['expires_at']:
            expired_locks.append(row_index)
            # If it was in editing state, enforce cooldown
            if lock['status'] == 'editing':
                row_locks[row_index] = {
                    'username': lock['username'],
                    'expires_at': now + timedelta(seconds=COOLDOWN_SECONDS),
                    'status': 'cooldown',
                    'last_modified': now
                }
                await broadcast_message({
                    "type": "lock_status",
                    "row_index": row_index,
                    "status": "cooldown",
                    "locked_by": lock['username'],
                    "expires_at": row_locks[row_index]['expires_at'].isoformat(),
                    "message": f"Row is in cooldown period for {COOLDOWN_SECONDS} seconds"
                })
                continue
            
    for row_index in expired_locks:
        if row_index in row_locks and row_locks[row_index]['status'] != 'cooldown':
            del row_locks[row_index]
            await broadcast_message({
                "type": "lock_status",
                "row_index": row_index,
                "locked_by": None,
                "status": "available",
                "message": "Lock expired and row is now available"
            })


async def connect_client(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket


async def disconnect_client(username: str):
    if username in active_connections:
        for row_index in list(row_locks.keys()):
            if row_locks[row_index]['username'] == username:
                del row_locks[row_index]
                await broadcast_message({
                    "type": "lock_status",
                    "row_index": row_index,
                    "locked_by": None
                })
        del active_connections[username]


def is_websocket_connected(websocket: WebSocket) -> bool:
    """Check if a WebSocket connection is still active."""
    try:
        return websocket.client_state.value == 1  # 1 means connected
    except Exception:
        return False


async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients."""
    print(f"Broadcasting message to {len(active_connections)} clients: {message['type']}")
    disconnected_users = []
    
    for username, connection in list(active_connections.items()):
        try:
            if is_websocket_connected(connection):
                try:
                    await connection.send_json(message)
                    print(f"Successfully sent to {username}")
                except RuntimeError as e:
                    if "already completed" in str(e) or "websocket.close" in str(e):
                        print(f"Connection already closed for {username}")
                        disconnected_users.append(username)
                    else:
                        print(f"Error sending to {username}: {e}")
                        disconnected_users.append(username)
            else:
                print(f"Connection not active for {username}")
                disconnected_users.append(username)
        except Exception as e:
            print(f"Error sending to {username}: {e}")
            disconnected_users.append(username)
    
    # Clean up disconnected users
    for username in disconnected_users:
        if username in active_connections:
            try:
                connection = active_connections[username]
                if is_websocket_connected(connection):
                    await connection.close(code=1000)
            except Exception:
                pass
            finally:
                if username in active_connections:
                    del active_connections[username]


async def broadcast_table_update(data: list, source_username: str = None):
    """Broadcast table updates to all connected clients."""
    print(f"Broadcasting table update from {source_username}")
    message = {
        "type": "csv_update",
        "data": data,
        "source": source_username,
        "timestamp": datetime.now().isoformat()
    }
    await broadcast_message(message)
    print("Table update broadcast completed")


async def broadcast_random_number(value: float, timestamp: str):
    await broadcast_message({
        "type": "random_number",
        "value": value,
        "timestamp": timestamp
    })


async def handle_lock_request(username: str, row_index: int):
    try:
        await validate_and_clean_locks()
        
        # Use a lock to prevent race conditions
        async with asyncio.Lock():
            # Check if row is locked by someone else
            if is_row_locked(row_index, username):
                if row_index in row_locks:
                    lock = row_locks[row_index]
                    remaining_time = int((lock['expires_at'] - datetime.now()).total_seconds() / 60)
                    message = (
                        f"Row is in cooldown period ({remaining_time} minutes remaining)"
                        if lock['status'] == 'cooldown'
                        else f"Row is being modified by {lock['username']}"
                    )
                    await broadcast_message({
                        "type": "lock_status",
                        "row_index": row_index,
                        "status": lock['status'],
                        "locked_by": lock['username'],
                        "expires_at": lock['expires_at'].isoformat(),
                        "message": message,
                        "source": username
                    })
                return False
            
            # If we get here, either there's no lock or the requesting user has the lock
            expires_at = datetime.now() + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
            row_locks[row_index] = {
                'username': username,
                'expires_at': expires_at,
                'status': 'editing',
                'last_modified': None  # Will be set when they save
            }
            
            await broadcast_message({
                "type": "lock_status",
                "row_index": row_index,
                "status": 'editing',
                "locked_by": username,
                "expires_at": expires_at.isoformat(),
                "message": f"{username} is modifying this row"
            })
            return True
            
    except Exception as e:
        print(f"Lock error: {e}")
        return False


async def handle_unlock_request(username: str, row_index: int):
    try:
        # Only the user who locked the row can unlock it
        if row_index not in row_locks or row_locks[row_index]['username'] != username:
            return False
        
        now = datetime.now()
        # Set cooldown period (now in seconds)
        expires_at = now + timedelta(seconds=COOLDOWN_SECONDS)
        row_locks[row_index] = {
            'username': username,
            'expires_at': expires_at,
            'status': 'cooldown',
            'last_modified': now
        }
        
        # Broadcast cooldown status
        await broadcast_message({
            "type": "lock_status",
            "row_index": row_index,
            "status": 'cooldown',
            "locked_by": username,
            "expires_at": expires_at.isoformat(),
            "message": f"Row is in cooldown period for {COOLDOWN_SECONDS} seconds"
        })
        
        return True
    except Exception as e:
        print(f"Unlock error: {e}")
        return False


async def remove_lock_after_cooldown(row_index: int, expires_at: datetime):
    try:
        await asyncio.sleep((expires_at - datetime.now()).total_seconds())
        if row_index in row_locks and row_locks[row_index]['expires_at'] == expires_at:
            del row_locks[row_index]
            await broadcast_message({
                "type": "lock_status",
                "row_index": row_index,
                "locked_by": None,
                "status": "available",
                "message": "Row is now available for editing"
            })
    except Exception as e:
        print(f"Error in cooldown cleanup: {e}")


async def send_ping(websocket: WebSocket):
    try:
        while True:
            try:
                await asyncio.sleep(10)
                if is_websocket_connected(websocket):
                    await websocket.send_json({"type": "ping"})
                else:
                    break
            except Exception as e:
                print(f"Error sending ping: {e}")
                break
    except asyncio.CancelledError:
        pass
    finally:
        print("Ping task ended")


async def process_messages(websocket: WebSocket, username: str):
    while True:
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "lock_row":
                row_index = message["row_index"]
                success = await handle_lock_request(username, row_index)
                try:
                    await websocket.send_json({
                        "type": "lock_status",
                        "row_index": row_index,
                        "locked_by": username if success else None,
                        "status": "editing" if success else "locked"
                    })
                except Exception as e:
                    print(f"Error sending lock status: {e}")
            
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


async def verify_lock_state(websocket: WebSocket, username: str):
    """Verify and sync lock states after reconnection"""
    try:
        # Send all current locks to the reconnected client
        for row_index, lock in row_locks.items():
            try:
                if is_websocket_connected(websocket):
                    await websocket.send_json({
                        "type": "lock_status",
                        "row_index": row_index,
                        "status": lock['status'],
                        "locked_by": lock['username'],
                        "expires_at": lock['expires_at'].isoformat(),
                        "message": "Lock state restored after reconnection"
                    })
            except Exception as e:
                print(f"Error sending lock status during verification: {e}")

        # If user had any locks, restore them
        for row_index, lock in list(row_locks.items()):
            if lock['username'] == username and lock['status'] == 'editing':
                # Extend the lock period
                lock['expires_at'] = datetime.now() + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
                await broadcast_message({
                    "type": "lock_status",
                    "row_index": row_index,
                    "status": "editing",
                    "locked_by": username,
                    "expires_at": lock['expires_at'].isoformat(),
                    "message": f"Lock restored for {username}"
                })
    except Exception as e:
        print(f"Error in verify_lock_state: {e}")


async def websocket_endpoint(websocket: WebSocket, username: str):
    cleanup_task = None
    ping_task = None
    message_task = None
    
    if not username or username.lower() == "null":
        try:
            await websocket.close(code=4001, reason="Username required")
        except Exception:
            pass
        return
    
    # Clean up any existing connection for this user
    if username in active_connections:
        old_connection = active_connections[username]
        try:
            if is_websocket_connected(old_connection):
                await old_connection.close(code=1000)
        except Exception:
            pass
        if username in active_connections:
            del active_connections[username]
    
    try:
        await websocket.accept()
        active_connections[username] = websocket
        print(f"WebSocket connected for user: {username}")
        
        # Verify and restore lock states
        await verify_lock_state(websocket, username)
        
        # Create tasks
        ping_task = asyncio.create_task(send_ping(websocket))
        message_task = asyncio.create_task(process_messages(websocket, username))
        cleanup_task = asyncio.create_task(periodic_lock_cleanup())
        
        # Wait for any task to complete (which usually means an error or disconnect)
        done, pending = await asyncio.wait(
            [ping_task, message_task, cleanup_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel other tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {username}")
    except Exception as e:
        print(f"WebSocket error for user {username}: {e}")
    finally:
        # Cancel any remaining tasks
        tasks = [t for t in [ping_task, message_task, cleanup_task] if t and not t.done()]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
        # Handle disconnection with grace period
        try:
            if username in active_connections and active_connections[username] == websocket:
                await asyncio.sleep(5)  # 5-second grace period
                if username in active_connections and active_connections[username] == websocket:
                    # Only clean up if this is still the active connection for the user
                    for row_index in list(row_locks.keys()):
                        if row_index in row_locks and row_locks[row_index]['username'] == username:
                            del row_locks[row_index]
                            try:
                                if websocket.client_state.state == "connected":
                                    await broadcast_message({
                                        "type": "lock_status",
                                        "row_index": row_index,
                                        "locked_by": None,
                                        "status": "available",
                                        "message": f"Row unlocked - {username} disconnected"
                                    })
                            except Exception as e:
                                print(f"Error broadcasting unlock message: {e}")
                    
                    if username in active_connections:
                        del active_connections[username]
        except Exception as e:
            print(f"Error in disconnect cleanup: {e}")


async def periodic_lock_cleanup():
    """Periodically clean up expired locks"""
    cleanup_interval = 5  # Check every 5 seconds
    
    try:
        while True:
            try:
                async with asyncio.Lock():
                    now = datetime.now()
                    expired_locks = []
                    
                    for row_index, lock in row_locks.items():
                        if now > lock['expires_at']:
                            if lock['status'] == 'editing':
                                # Convert to cooldown state
                                row_locks[row_index] = {
                                    'username': lock['username'],
                                    'expires_at': now + timedelta(seconds=COOLDOWN_SECONDS),
                                    'status': 'cooldown',
                                    'last_modified': now
                                }
                                await broadcast_message({
                                    "type": "lock_status",
                                    "row_index": row_index,
                                    "status": "cooldown",
                                    "locked_by": lock['username'],
                                    "expires_at": row_locks[row_index]['expires_at'].isoformat(),
                                    "message": f"Row is in cooldown period for {COOLDOWN_SECONDS} seconds"
                                })
                            elif lock['status'] == 'cooldown':
                                expired_locks.append(row_index)
                    
                    # Remove expired cooldown locks
                    for row_index in expired_locks:
                        if row_index in row_locks:
                            del row_locks[row_index]
                            await broadcast_message({
                                "type": "lock_status",
                                "row_index": row_index,
                                "locked_by": None,
                                "status": "available",
                                "message": "Row is now available for editing"
                            })
                            
            except Exception as e:
                print(f"Error in cleanup iteration: {e}")
                
            await asyncio.sleep(cleanup_interval)
            
    except asyncio.CancelledError:
        print("Lock cleanup task cancelled")
    except Exception as e:
        print(f"Fatal error in lock cleanup: {e}")
    finally:
        print("Lock cleanup task ended")