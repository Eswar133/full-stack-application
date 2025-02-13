from fastapi import APIRouter, Depends, HTTPException, WebSocket, Request
from auth import verify_token
from auth import router as auth_router
from database import get_db_connection
from file_opeartions import (
    read_csv, update_csv_entry, delete_csv_entry, append_csv_entry, 
    restore_backup, RowLockError
)
from websocket import websocket_endpoint
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

class CSVEntry(BaseModel):
    user: Optional[str] = Field(default="")
    broker: Optional[str] = Field(default="")
    API_key: Optional[str] = Field(default="", alias="API key")
    API_secret: Optional[str] = Field(default="", alias="API secret")
    pnl: Optional[float] = Field(default=0.0)
    margin: Optional[float] = Field(default=0.0)
    max_risk: Optional[float] = Field(default=0.0)

    class Config:
        allow_population_by_field_name = True

# ✅ Fetch Random Numbers
@router.get("/numbers", dependencies=[Depends(verify_token)])
def get_numbers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM random_numbers ORDER BY timestamp DESC LIMIT 100")
    data = cursor.fetchall()
    conn.close()
    return data

# ✅ Fetch CSV File (Read)
@router.get("/fetch_csv")
async def fetch_csv(request: Request, _: str = Depends(verify_token)) -> List[Dict[str, Any]]:
    """Fetch the CSV data."""
    try:
        return read_csv()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Add new entry to CSV (Create)
@router.post("/add_csv")
async def add_csv(request: Request, data: CSVEntry, _: str = Depends(verify_token)):
    try:
        username = request.state.username
        entry_data = {
            "user": data.user or "",
            "broker": data.broker or "",
            "API key": data.API_key or "",
            "API secret": data.API_secret or "",
            "pnl": float(data.pnl) if data.pnl else 0.0,
            "margin": float(data.margin) if data.margin else 0.0,
            "max_risk": float(data.max_risk) if data.max_risk else 0.0
        }
        await append_csv_entry(entry_data, username)
        return {"message": "Entry added successfully"}
    except Exception as e:
        # ✅ Return detailed error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add entry: {str(e)}"
        )
# ✅ Update an entry in CSV (Update)
@router.put("/update_csv/{index}")
async def update_csv(index: int, data: CSVEntry, request: Request, _: str = Depends(verify_token)):
    """Update an existing entry in the CSV file."""
    try:
        username = request.state.username
        entry_data = {
            "user": data.user,
            "broker": data.broker,
            "API key": data.API_key,
            "API secret": data.API_secret,
            "pnl": data.pnl,
            "margin": data.margin,
            "max_risk": data.max_risk
        }
        await update_csv_entry(index, entry_data, username)
        return {"message": "Entry updated successfully"}
    except RowLockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Delete an entry from CSV (Delete)
@router.delete("/delete_csv/{index}")
async def delete_csv(index: int, request: Request, _: str = Depends(verify_token)):
    """Delete an entry from the CSV file."""
    try:
        username = request.state.username
        await delete_csv_entry(index, username)
        return {"message": "Entry deleted successfully"}
    except RowLockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ WebSocket for Real-time Data
@router.websocket("/ws")
async def websocket_route(websocket: WebSocket, username: str = None):
    """WebSocket endpoint for real-time updates."""
    if not username:
        await websocket.close(code=4000, reason="Username is required")
        return
    await websocket_endpoint(websocket, username)

router.include_router(auth_router, prefix="")
