import asyncio
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from routes import router
from database import init_db
from websocket import websocket_endpoint, active_connections
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Add root endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# Get allowed origins from environment variable
ALLOWED_ORIGINS = [
    "https://dashflow-3clbiykeb-eswar133s-projects.vercel.app",
    "https://dashflow-r0upi26x3-eswar133s-projects.vercel.app",
    "http://localhost:3000",
    "https://full-stack-application-spz2.onrender.com"
]

# ✅ Enable CORS with environment variables
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
