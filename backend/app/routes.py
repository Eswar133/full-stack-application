from fastapi import APIRouter, Depends, HTTPException, WebSocket
from auth import verify_token
from auth import router as auth_router
from database import get_db_connection
from file_opeartions import read_csv, update_csv_entry, delete_csv_entry, append_csv_entry  # ✅ Fixed imports
from websocket import websocket_endpoint

router = APIRouter()

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
@router.get("/fetch_csv", dependencies=[Depends(verify_token)])
def fetch_csv():
    return read_csv()

# ✅ Add new entry to CSV (Create)
@router.post("/add_csv", dependencies=[Depends(verify_token)])
def add_csv_entry(new_data: dict):
    try:
        append_csv_entry(new_data)
        return {"message": "New row added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Update an entry in CSV (Update)
@router.put("/update_csv/{index}", dependencies=[Depends(verify_token)])
def update_csv(index: int, new_data: dict):
    try:
        update_csv_entry(index, new_data)
        return {"message": "Row updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Delete an entry from CSV (Delete)
@router.delete("/delete_csv/{index}", dependencies=[Depends(verify_token)])
def delete_csv(index: int):
    try:
        delete_csv_entry(index)
        return {"message": "Row deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ WebSocket for Real-time Data
@router.websocket("/ws")
async def websocket(ws: WebSocket):
    await websocket_endpoint(ws)

router.include_router(auth_router, prefix="")
