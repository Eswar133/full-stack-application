import pandas as pd
import os
import shutil
from filelock import FileLock

CSV_FILE = "backend_table.csv"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# ✅ Ensure CSV file exists before performing operations
def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=["User", "Broker", "PNL"])  # Adjust columns as needed
        df.to_csv(CSV_FILE, index=False)

# ✅ Create Backup before modification
def create_backup():
    ensure_csv_exists()
    backup_path = os.path.join(BACKUP_DIR, f"backup_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.csv")
    shutil.copy(CSV_FILE, backup_path)

# ✅ Read CSV file and return as dictionary
def read_csv():
    ensure_csv_exists()
    return pd.read_csv(CSV_FILE).to_dict(orient="records")

# ✅ Append a new entry to CSV (Create Operation)
def append_csv_entry(new_data):
    ensure_csv_exists()
    with FileLock(f"{CSV_FILE}.lock"):
        df = pd.read_csv(CSV_FILE)
        df = df.append(new_data, ignore_index=True)  # Append new row
        df.to_csv(CSV_FILE, index=False)

# ✅ Update an existing entry (Update Operation)
def update_csv_entry(index, new_data):
    ensure_csv_exists()
    with FileLock(f"{CSV_FILE}.lock"):
        df = pd.read_csv(CSV_FILE)
        
        if index >= len(df):
            raise ValueError("Invalid row index")
        
        for key, value in new_data.items():
            if key in df.columns:
                df.at[index, key] = value  # Update specific column
        
        create_backup()
        df.to_csv(CSV_FILE, index=False)

# ✅ Delete an entry from CSV (Delete Operation)
def delete_csv_entry(index):
    ensure_csv_exists()
    with FileLock(f"{CSV_FILE}.lock"):
        df = pd.read_csv(CSV_FILE)
        
        if index >= len(df):
            raise ValueError("Invalid row index")
        
        df = df.drop(index)  # Remove row
        create_backup()
        df.to_csv(CSV_FILE, index=False)
