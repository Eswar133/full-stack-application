import asyncio
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from database import init_db

app = FastAPI()

# ✅ Enable CORS (Required for Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Initialize the database
init_db()

# ✅ Include all API routes
app.include_router(router)

# ✅ Background Task to Generate Random Numbers
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_numbers())

async def generate_numbers():
    while True:
        timestamp = datetime.now().isoformat()
        value = random.randint(0, 100)

        conn = sqlite3.connect("backend.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO random_numbers (timestamp, value) VALUES (?, ?)", (timestamp, value))
        conn.commit()
        conn.close()

        await asyncio.sleep(1)  # ✅ Generate a new number every second

# ✅ Run FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
