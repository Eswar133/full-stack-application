import os
import pandas as pd
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from fastapi import WebSocket
import asyncio
from websocket import broadcast_table_update

# Get the CSV file path from environment variables
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', '/opt/render/project/src/backend/data/backend_table.csv')
CSV_BACKUP_DIR = os.getenv('CSV_BACKUP_DIR', '/opt/render/project/src/backend/data/backups')

# Ensure directories exist
os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)
os.makedirs(CSV_BACKUP_DIR, exist_ok=True)

class RowLockError(Exception):
    pass

def ensure_csv_exists():
    """Ensure the CSV file exists with the required columns."""
    if not os.path.exists(CSV_FILE_PATH):
        print(f"CSV file not found, creating new one at: {CSV_FILE_PATH}")
        # Create an empty DataFrame with the required columns
        df = pd.DataFrame(columns=[
            'user', 'broker', 'API key', 'API secret', 'pnl', 'margin', 'max_risk'
        ])
        
        # Add a sample row
        sample_row = {
            'user': 'sample_user',
            'broker': 'sample_broker',
            'API key': 'sample_key',
            'API secret': 'sample_secret',
            'pnl': 0.0,
            'margin': 0.0,
            'max_risk': 0.0
        }
        df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)
        
        # Save to CSV
        df.to_csv(CSV_FILE_PATH, index=False)
        print("Created new CSV file with empty template")
    else:
        print(f"CSV file exists at: {CSV_FILE_PATH}")

def create_backup():
    """Create a backup of the current CSV file."""
    if os.path.exists(CSV_FILE_PATH):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(CSV_BACKUP_DIR, f'backup_{timestamp}.csv')
        shutil.copy2(CSV_FILE_PATH, backup_path)
        
        # Clean up old backups (keep last 10)
        backups = sorted([f for f in os.listdir(CSV_BACKUP_DIR) if f.startswith('backup_')])
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(os.path.join(CSV_BACKUP_DIR, old_backup))

def read_csv() -> List[Dict[str, Any]]:
    """Read the CSV file and return its contents as a list of dictionaries."""
    print(f"Reading CSV from: {CSV_FILE_PATH}")
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE_PATH)
    return df.to_dict('records')

async def update_csv_entry(index: int, entry: Dict[str, Any], username: str):
    """Update a specific entry in the CSV file."""
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE_PATH)
    
    if index < 0 or index >= len(df):
        raise ValueError(f"Invalid index: {index}")
    
    create_backup()
    df.loc[index] = entry
    df.to_csv(CSV_FILE_PATH, index=False)
    
    # Broadcast the update to all connected clients
    await broadcast_table_update(df.to_dict('records'), username)

async def delete_csv_entry(index: int, username: str):
    """Delete a specific entry from the CSV file."""
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE_PATH)
    
    if index < 0 or index >= len(df):
        raise ValueError(f"Invalid index: {index}")
    
    create_backup()
    df = df.drop(index)
    df = df.reset_index(drop=True)
    df.to_csv(CSV_FILE_PATH, index=False)
    
    # Broadcast the update to all connected clients
    await broadcast_table_update(df.to_dict('records'), username)

async def append_csv_entry(entry: Dict[str, Any], username: str):
    """Append a new entry to the CSV file."""
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE_PATH)
    
    create_backup()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(CSV_FILE_PATH, index=False)
    
    # Broadcast the update to all connected clients
    await broadcast_table_update(df.to_dict('records'), username)

def restore_backup(backup_name: str):
    """Restore a specific backup file."""
    backup_path = os.path.join(CSV_BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        raise ValueError(f"Backup file not found: {backup_name}")
    
    shutil.copy2(backup_path, CSV_FILE_PATH)
