"""
Seed Script — Populate MongoDB with sample waste events
────────────────────────────────────────────────────────
Inserts 15 realistic records into the smart_segro.waste_logs
collection so the dashboard has data to display immediately.

Usage:
    cd backend
    python seed_db.py
"""

import os
import sys
import random
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Fix Windows console encoding for emoji / Unicode
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


def seed_database():
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("[ERROR] MONGODB_URI not found in .env file.")
        return

    try:
        print("[*] Connecting to MongoDB...")
        client     = MongoClient(mongo_uri)
        db         = client.smart_segro        # same DB as the FastAPI app
        collection = db.waste_logs             # same collection

        waste_types = ["Metal", "Plastic"]
        now = datetime.now(timezone.utc)
        records = []

        for _ in range(15):
            ts = now - timedelta(minutes=random.randint(1, 120))
            records.append({
                "waste_type": random.choice(waste_types),
                "status":     "Collected",
                "timestamp":  ts,
            })

        # Sort oldest-first so _id ordering matches timestamp ordering
        records.sort(key=lambda r: r["timestamp"])

        result = collection.insert_many(records)
        print(f"[OK] Inserted {len(result.inserted_ids)} sample records into smart_segro.waste_logs")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    seed_database()
