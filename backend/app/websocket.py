import json
import sqlite3
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from datetime import datetime, timedelta
import pytz

# Constants for lock timeouts
EDIT_TIMEOUT_MINUTES = 15  # Maximum time a user can hold a lock
COOLDOWN_SECONDS = 5      # Cooldown period after editing

# Add IST and UTC timezones
ist = pytz.timezone('Asia/Kolkata')
utc = pytz.UTC

active_connections: Dict[str, WebSocket] = {}
row_locks: Dict[int, dict] = {}  # Stores {row_index: {username, expires_at, status, last_modified}}

async def validate_lock_request(row_index: int, username: str):
    """Validate lock request with proper error handling"""
    if row_index not in row_locks:
        return True, None
        
    lock = row_locks[row_index]
    now = datetime.now(utc)
    
    if now > lock['expires_at']:
        return True, None
        
    if lock['status'] == 'cooldown':
        remaining = (lock['expires_at'] - now).total_seconds()
        return False, f"Row is in cooldown ({int(remaining)} seconds remaining)"
        
    if lock['username'] != username:
        return False, f"Row is being edited by {lock['username']}"
        
    return True, None

def is_row_locked(row_index: int, requesting_user: str) -> bool:
    """Check if a row is locked by another user."""
    if row_index not in row_locks:
        return False
    
    lock = row_locks[row_index]
    now = datetime.now(utc)
    
    # If lock has expired, clean it up
    if now > lock['expires_at']:
        if lock['status'] == 'editing':
            # Convert to cooldown
            row_locks[row_index] = {
                'username': lock['username'],
                'expires_at': now + timedelta(seconds=COOLDOWN_SECONDS),
                'status': 'cooldown',
                'last_modified': now
            }
            return True
        else:
            del row_locks[row_index]
            return False
    
    # If the row is in cooldown, it's locked for everyone
    if lock['status'] == 'cooldown':
        return True
    
    # If someone else has the lock, it's locked
    if lock['username'] != requesting_user:
        return True
    
    # The requesting user has the lock
    return False

async def broadcast_message(message: dict, exclude: list = None):
    """Broadcast a message to all connected clients except those in exclude list."""
    if exclude is None:
        exclude = []
    
    print(f"Broadcasting message to {len(active_connections)} clients: {message['type']}")
    disconnected_users = []
    
    for username, connection in list(active_connections.items()):
        if username in exclude:
            continue
            
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

async def handle_lock_request(username: str, row_index: int):
    """Handle a request to lock a row for editing."""
    try:
        # Use a lock to prevent race conditions
        async with asyncio.Lock():
            # Check if user already has this lock
            if row_index in row_locks and row_locks[row_index]['username'] == username:
                # Refresh the lock
                now = datetime.now(utc)
                expires_at = now + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
                row_locks[row_index]['expires_at'] = expires_at
                row_locks[row_index]['last_modified'] = now
                
                await active_connections[username].send_json({
                    "type": "lock_confirmation",
                    "row_index": row_index,
                    "status": "editing",
                    "expires_at": expires_at.isoformat(),
                    "message": "Lock refreshed successfully"
                })
                return True

            # Validate lock request
            is_valid, error_message = await validate_lock_request(row_index, username)
            if not is_valid:
                if username in active_connections:
                    await active_connections[username].send_json({
                        "type": "lock_denied",
                        "row_index": row_index,
                        "message": error_message
                    })
                return False
            
            # Grant the lock
            now = datetime.now(utc)
            expires_at = now + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
            row_locks[row_index] = {
                'username': username,
                'expires_at': expires_at,
                'status': 'editing',
                'last_modified': now
            }
            
            # Send direct confirmation to requester immediately
            if username in active_connections:
                try:
                    await active_connections[username].send_json({
                        "type": "lock_confirmation",
                        "row_index": row_index,
                        "status": "editing",
                        "expires_at": expires_at.isoformat(),
                        "message": "Lock acquired successfully"
                    })
                except Exception as e:
                    print(f"Error sending lock confirmation to {username}: {e}")
                    return False
            
            # Broadcast to others
            try:
                await broadcast_message({
                    "type": "lock_status",
                    "row_index": row_index,
                    "status": 'editing',
                    "locked_by": username,
                    "expires_at": expires_at.isoformat(),
                    "message": f"{username} is editing this row"
                }, exclude=[username])
            except Exception as e:
                print(f"Error broadcasting lock status: {e}")
            
            return True
            
    except Exception as e:
        print(f"Lock error: {e}")
        if username in active_connections:
            try:
                await active_connections[username].send_json({
                    "type": "lock_denied",
                    "row_index": row_index,
                    "message": f"Lock request failed: {str(e)}"
                })
            except Exception:
                pass
        return False

async def restore_user_locks(username: str, websocket: WebSocket):
    """Restore user's locks after reconnection"""
    now = datetime.now(utc)
    for row_index, lock in list(row_locks.items()):
        if lock['username'] == username and lock['status'] == 'editing':
            if now > lock['expires_at']:
                # Convert to cooldown if expired
                await handle_unlock_request(username, row_index)
            else:
                # Refresh the lock
                lock['expires_at'] = now + timedelta(minutes=EDIT_TIMEOUT_MINUTES)
                await websocket.send_json({
                    "type": "lock_restored",
                    "row_index": row_index,
                    "expires_at": lock['expires_at'].isoformat(),
                    "message": "Your lock has been restored"
                })

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

        # Restore user's locks
        await restore_user_locks(username, websocket)
        
    except Exception as e:
        print(f"Error in verify_lock_state: {e}")

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


async def broadcast_table_update(data: list, source_username: str = None):
    """Broadcast table updates to all connected clients."""
    print(f"Broadcasting table update from {source_username}")
    current_time = datetime.now(ist)
    message = {
        "type": "csv_update",
        "data": data,
        "source": source_username,
        "timestamp": current_time.isoformat()
    }
    await broadcast_message(message)
    print("Table update broadcast completed")


# Format timestamp without seconds, using IST
def format_time(dt):
    # Ensure the timestamp is in IST
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = pytz.utc.localize(dt).astimezone(ist)
    elif dt.tzinfo != ist:
        dt = dt.astimezone(ist)
    return dt.strftime('%H:%M')  # 24-hour format without seconds


async def broadcast_random_number(value: float, timestamp: str):
    try:
        # Get current time in IST
        current_time = datetime.now(ist)
        
        # Format current time without seconds
        current_time_str = format_time(current_time)
        
        await broadcast_message({
            "type": "random_number",
            "value": value,
            "timestamp": current_time_str
        })
    except Exception as e:
        print(f"Error in broadcast_random_number: {e}")
        # Fallback to current IST time if there's an error
        current_time = datetime.now(ist)
        await broadcast_message({
            "type": "random_number",
            "value": value,
            "timestamp": format_time(current_time)
        })


async def handle_unlock_request(username: str, row_index: int):
    """Handle a request to unlock a row."""
    try:
        if row_index not in row_locks:
            return True
            
        lock = row_locks[row_index]
        if lock['username'] != username:
            return False
            
        # Set cooldown period
        now = datetime.now()
        expires_at = now + timedelta(seconds=COOLDOWN_SECONDS)
        row_locks[row_index] = {
            'username': username,
            'expires_at': expires_at,
            'status': 'cooldown',
            'last_modified': now
        }
        
        await broadcast_message({
            "type": "lock_status",
            "row_index": row_index,
            "status": 'cooldown',
            "locked_by": username,
            "expires_at": expires_at.isoformat(),
            "message": f"Row is in cooldown period for {COOLDOWN_SECONDS} seconds"
        })
        
        # Schedule lock removal after cooldown
        asyncio.create_task(remove_lock_after_cooldown(row_index, expires_at))
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
    
    try:
        # Accept the connection first
        await websocket.accept()
        print(f"WebSocket connected for user: {username}")
        
        # Clean up any existing connection for this user
        if username in active_connections:
            old_connection = active_connections[username]
            try:
                if is_websocket_connected(old_connection):
                    await old_connection.close(code=1000)
            except Exception:
                pass
        
        # Store the new connection
        active_connections[username] = websocket
        
        # Verify and restore lock states
        await verify_lock_state(websocket, username)
        
        # Create tasks
        ping_task = asyncio.create_task(send_ping(websocket))
        message_task = asyncio.create_task(process_messages(websocket, username))
        cleanup_task = asyncio.create_task(periodic_lock_cleanup())
        
        # Wait for any task to complete
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
            
        # Handle disconnection
        if username in active_connections:
            del active_connections[username]
            
        # Clean up locks
        for row_index in list(row_locks.keys()):
            if row_index in row_locks and row_locks[row_index]['username'] == username:
                del row_locks[row_index]
                try:
                    await broadcast_message({
                        "type": "lock_status",
                        "row_index": row_index,
                        "locked_by": None,
                        "status": "available",
                        "message": f"Row unlocked - {username} disconnected"
                    })
                except Exception as e:
                    print(f"Error broadcasting unlock message: {e}")


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