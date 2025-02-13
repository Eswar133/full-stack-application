import json
import sqlite3
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            conn = sqlite3.connect("backend.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM random_numbers ORDER BY timestamp DESC LIMIT 1")
            data = cursor.fetchone()
            conn.close()

            if data:
                await websocket.send_text(json.dumps({"timestamp": data[0], "value": data[1]}))
            
            await asyncio.sleep(1)  # Send new data every second
    except WebSocketDisconnect:
        print("WebSocket client disconnected")  # ✅ Handle disconnections gracefully
    except Exception as e:
        print(f"WebSocket Error: {str(e)}")  # ✅ Log unexpected errors
    finally:
        await websocket.close()
