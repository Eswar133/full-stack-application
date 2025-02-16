import asyncio
import sqlite3
import random
from datetime import datetime
import pytz
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from routes import router
from database import init_db
from websocket import websocket_endpoint, active_connections, broadcast_random_number
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add IST timezone
ist = pytz.timezone('Asia/Kolkata')

app = FastAPI()

# Add root endpoint
@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

# Get allowed origins from environment variable
ALLOWED_ORIGINS = [
    "https://dashflow-hr6opecps-eswar133s-projects.vercel.app",
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
    prev_value = 50  # Starting value
    while True:
        try:
            # Get current time in IST
            current_time = datetime.now(ist)
            
            # Generate new value by adding/subtracting up to 10 from previous value
            change = random.uniform(-10, 10)
            value = max(0, min(100, prev_value + change))  # Keep between 0 and 100
            prev_value = value

            # Store in database with IST timestamp
            conn = sqlite3.connect("backend.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO random_numbers (timestamp, value) VALUES (?, ?)", 
                (current_time.isoformat(), value)
            )
            conn.commit()
            conn.close()

            # Broadcast to all connected clients with IST time
            await broadcast_random_number(value, current_time)
            await asyncio.sleep(1)  # Generate a new number every second
            
        except Exception as e:
            print(f"Error in generate_numbers: {e}")
            await asyncio.sleep(1)  # Wait before retrying

# ✅ Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
