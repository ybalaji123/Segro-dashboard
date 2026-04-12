"""
Smart Segro — FastAPI Backend
──────────────────────────────
• POST /api/sensor-data      ← ESP32 sends waste detection events
• GET  /api/dashboard-data   ← Frontend polls every 2 s for live counts + recent logs
• Serves the vanilla HTML/CSS/JS dashboard from the /frontend directory
"""

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# ── Configuration ───────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

MONGO_URI    = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME      = "smart_segro"
COLLECTION   = "waste_logs"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


# ── MongoDB lifecycle ───────────────────────────────────────────────────────
motor_client: AsyncIOMotorClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the Motor client on startup, close on shutdown."""
    global motor_client
    motor_client = AsyncIOMotorClient(MONGO_URI)
    # Quick connectivity check (will raise on bad URI before accepting traffic)
    await motor_client.admin.command("ping")
    print("[OK] Connected to MongoDB")
    yield
    motor_client.close()
    print("[--] MongoDB connection closed")


def get_collection():
    """Return the waste_logs collection handle."""
    return motor_client[DB_NAME][COLLECTION]


# ── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Segro API",
    description="Backend for Smart Waste Segregation Dustbin (ESP32)",
    lifespan=lifespan,
)

# Allow all origins so the ESP32 on the local hotspot LAN can POST freely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Data Model ──────────────────────────────────────────────────────────────
class SensorData(BaseModel):
    """Payload the ESP32 sends after each detection."""
    waste_type: str = Field(..., description='Material type — e.g. "Metal" or "Plastic"')
    status: str     = Field(..., description='Drop status — e.g. "Collected"')


# ── API Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/sensor-data", summary="ESP32 → Save waste detection event")
async def receive_sensor_data(data: SensorData):
    """
    Receive a waste detection event from the ESP32, add a server-side
    timestamp, and persist it to MongoDB.

    Expected JSON body::

        {"waste_type": "Metal", "status": "Collected"}
    """
    document = {
        "waste_type": data.waste_type,
        "status":     data.status,
        "timestamp":  datetime.now(timezone.utc),
    }

    result = await get_collection().insert_one(document)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save data to MongoDB")

    return {
        "status":  "success",
        "message": "Data saved to MongoDB",
        "id":      str(result.inserted_id),
    }


@app.get("/api/dashboard-data", summary="Frontend → Get counts + recent activity")
async def get_dashboard_data():
    """
    Returns:
    - total_processed  : total number of waste events recorded
    - metals_count     : events where waste_type == "Metal"
    - plastics_count   : all remaining (non-metal) events
    - recent_activity  : last 5 log entries (newest first)
    """
    col = get_collection()

    total  = await col.count_documents({})
    metals = await col.count_documents({"waste_type": {"$regex": "^metal$", "$options": "i"}})
    plastics = total - metals

    cursor = col.find().sort("timestamp", -1).limit(5)
    recent = []
    async for doc in cursor:
        ts = doc.get("timestamp")
        recent.append({
            "id":         str(doc["_id"]),
            "waste_type": doc.get("waste_type", "Unknown"),
            "status":     doc.get("status", "—"),
            "timestamp":  ts.isoformat() if isinstance(ts, datetime) else str(ts or ""),
        })

    return {
        "total_processed": total,
        "metals_count":    metals,
        "plastics_count":  plastics,
        "recent_activity": recent,
    }


# ── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", summary="Health check")
async def health():
    return {
        "status":             "ok",
        "esp32_endpoint":     "POST /api/sensor-data",
        "dashboard_endpoint": "GET /api/dashboard-data",
        "dashboard_ui":       "GET /",
    }


# ── Serve Frontend ──────────────────────────────────────────────────────────
# index.html at root, static assets (style.css, script.js) alongside it

@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the dashboard HTML at the root URL."""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# Mount static assets *after* API routes so API routes take priority
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend-static")