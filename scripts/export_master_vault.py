import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

db_path = Path("data/autopilot.db")
if not db_path.exists():
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row["name"] for row in cursor.fetchall() if not row["name"].startswith("sqlite_")]

vault_data = {
    "exported_at": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0",
    "founder_admin": "admin_abhay (Abhay Maurya)",
    "tables_summary": {},
    "data": {}
}

for tbl in tables:
    cursor.execute(f"SELECT * FROM {tbl}")
    rows = [dict(r) for r in cursor.fetchall()]
    vault_data["tables_summary"][tbl] = len(rows)
    vault_data["data"][tbl] = rows
    print(f"Exported {tbl:22}: {len(rows)} records")

out_file = Path("data/autopilot_master_vault_backup.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(vault_data, f, indent=2, default=str)

print(f"\nSuccessfully wrote master backup to {out_file} ({out_file.stat().st_size / 1024 / 1024:.2f} MB)")
