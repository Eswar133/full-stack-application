import asyncio
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from database import init_db
from websocket import websocket_endpoint, active_connections
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# ✅ Enable CORS with environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=eval(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Initialize the database
init_db()

# ✅ Include all API routes
app.include_router(router, prefix="/api")

# ✅ WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_route(websocket: WebSocket, username: str = None):
    await websocket_endpoint(websocket, username)

# ✅ Background Task to Generate Random Numbers
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_numbers())

async def generate_numbers():
    """Generate random numbers and broadcast to all connected clients."""
    while True:
        try:
            timestamp = datetime.now().isoformat()
            value = random.randint(0, 100)

            # Store in database
            conn = sqlite3.connect("backend.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO random_numbers (timestamp, value) VALUES (?, ?)", (timestamp, value))
            conn.commit()
            conn.close()

            # Broadcast to all connected clients
            message = {
                "type": "random_number",
                "timestamp": timestamp,
                "value": value
            }
            
            for ws in active_connections.values():
                try:
                    await ws.send_json(message)
                except Exception as e:
                    print(f"Error sending to WebSocket: {e}")

            await asyncio.sleep(1)  # Generate a new number every second
        except Exception as e:
            print(f"Error in generate_numbers: {e}")
            await asyncio.sleep(1)  # Wait before retrying

# ✅ Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
