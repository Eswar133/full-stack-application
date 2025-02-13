import pandas as pd
import os
import shutil
from datetime import datetime
from filelock import FileLock
from websocket import broadcast_table_update, is_row_locked
import numpy as np

# Get the absolute path to the backend/app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "backend_table.csv")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

class RowLockError(Exception):
    """Exception raised when attempting to modify a locked row."""
    pass


def ensure_csv_exists():
    """Ensure CSV file exists with proper columns."""
    required_columns = [
        "user", "broker", "API key", "API secret", 
        "pnl", "margin", "max_risk"
    ]
    
    print(f"Checking CSV at: {CSV_FILE}")
    
    if not os.path.exists(CSV_FILE):
        print(f"CSV file not found, creating new one at: {CSV_FILE}")
        # Create new CSV with required columns
        df = pd.DataFrame(columns=required_columns)
        # Add a sample row
        sample_row = {
            "user": "sample_user",
            "broker": "sample_broker",
            "API key": "sample_key",
            "API secret": "sample_secret",
            "pnl": 0.0,
            "margin": 0.0,
            "max_risk": 0.0
        }
        df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        print(f"Created new CSV file with sample data")
    else:
        print(f"CSV file exists at: {CSV_FILE}")
        # Verify and fix existing CSV
        try:
            df = pd.read_csv(CSV_FILE)
            # Add any missing columns
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ""
            # Convert numeric columns
            df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
            df["margin"] = pd.to_numeric(df["margin"], errors="coerce").fillna(0.0)
            df["max_risk"] = pd.to_numeric(df["max_risk"], errors="coerce").fillna(0.0)
            df.to_csv(CSV_FILE, index=False)
        except Exception as e:
            print(f"Error reading CSV: {e}")
            # Create new CSV if existing one is corrupted
            df = pd.DataFrame(columns=required_columns)
            df.to_csv(CSV_FILE, index=False)



# ✅ Create Backup before modification
def create_backup():
    """Create a backup of the CSV file."""
    ensure_csv_exists()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.csv")
    shutil.copy(CSV_FILE, backup_path)
    return backup_path

# ✅ Read CSV file and return as dictionary with proper float handling
def read_csv():
    """Read CSV file and return as dictionary with proper float handling."""
    ensure_csv_exists()
    try:
        print(f"Reading CSV from: {CSV_FILE}")
        df = pd.read_csv(CSV_FILE)
        # Convert float values to Python floats
        float_cols = ['pnl', 'margin', 'max_risk']
        for col in float_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            df[col] = df[col].replace([np.inf, -np.inf], None)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

# ✅ Update an existing entry (Update Operation)
async def update_csv_entry(index: int, new_data: dict, username: str):
    """Update an existing entry with row locking."""
    if not username:
        raise ValueError("Username is required")
    
    if is_row_locked(index, username):
        raise RowLockError(f"Row {index} locked by another user")
    
    ensure_csv_exists()
    try:
        with FileLock(f"{CSV_FILE}.lock"):
            df = pd.read_csv(CSV_FILE)
            
            if index >= len(df):
                raise ValueError("Invalid row index")
            
            # Update the row with new data and metadata
            for key, value in new_data.items():
                if key in df.columns:
                    df.at[index, key] = value
            
            create_backup()
            df.to_csv(CSV_FILE, index=False)
    
    finally:
        if index in row_locks and row_locks[index][0] == username:
            del row_locks[index]
            await broadcast_message({
                "type": "lock_status",
                "row_index": index,
                "locked_by": None
            })

    await broadcast_table_update(read_csv())
# ✅ Delete an entry from CSV (Delete Operation)
async def delete_csv_entry(index: int, username: str):
    """Delete an entry with row locking."""
    if is_row_locked(index, username):
        raise RowLockError("This row is currently being edited by another user")

    ensure_csv_exists()
    with FileLock(f"{CSV_FILE}.lock"):
        df = pd.read_csv(CSV_FILE)
        
        if index >= len(df):
            raise ValueError("Invalid row index")
        
        df = df.drop(index)
        create_backup()
        df.to_csv(CSV_FILE, index=False)
        
        # Convert float values for JSON serialization
        float_cols = ['pnl', 'margin', 'max_risk']
        for col in float_cols:
            df[col] = df[col].astype(float)
            df[col] = df[col].replace([np.inf, -np.inf], None)
        
        # Broadcast the update
        await broadcast_table_update(df.to_dict(orient="records"))

async def append_csv_entry(new_data: dict, username: str):
    """Append a new entry to the CSV file."""
    ensure_csv_exists()
    with FileLock(f"{CSV_FILE}.lock"):
        df = pd.read_csv(CSV_FILE)
        
        # ✅ Correct default data structure (remove unwanted fields)
        default_data = {
            "user": "",
            "broker": "",
            "API key": "",
            "API secret": "",
            "pnl": 0.0,
            "margin": 0.0,
            "max_risk": 0.0
        }
        
        # Convert numeric fields
        for key in ['pnl', 'margin', 'max_risk']:
            if key in new_data:
                try:
                    new_data[key] = float(new_data[key] or 0)
                except (ValueError, TypeError):
                    new_data[key] = 0.0

        # Merge with default values
        merged_data = {**default_data, **new_data}
        
        # ✅ Create new row with proper data types
        new_row = pd.DataFrame([merged_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        create_backup()
        df.to_csv(CSV_FILE, index=False)
        await broadcast_table_update(df.to_dict(orient="records"))
        print(f"Writing to: {os.path.abspath(CSV_FILE)}")
        
def restore_backup(backup_timestamp: str, username: str):
    """Restore from a backup file."""
    backup_path = os.path.join(BACKUP_DIR, f"backup_{backup_timestamp}.csv")
    if not os.path.exists(backup_path):
        raise ValueError("Backup file not found")

    with FileLock(f"{CSV_FILE}.lock"):
        # Create a backup of current state before restoring
        create_backup()
        
        # Copy backup file to main CSV
        shutil.copy(backup_path, CSV_FILE)
        
        # Read and return the restored data
        return read_csv()
