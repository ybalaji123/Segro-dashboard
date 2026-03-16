from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import List, Optional
from datetime import datetime

# Load environment variables (your MongoDB connection string)
load_dotenv()

app = FastAPI(title="Smart Dustbin API")

# Add CORS middleware to allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB asynchronously
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.smart_dustbin
collection = db.sensor_readings

# Define the structure of the data coming from the ESP32
class SensorData(BaseModel):
    ultrasonic_distance: float
    inductive: int
    capacitive: int
    waste_category: str
    fill_percentage: Optional[float] = 0.0 # Percentage filled
    timestamp: datetime = datetime.now()

@app.post("/api/data")
async def receive_data(data: SensorData):
    """Endpoint for the ESP32 to send sensor data."""
    document = data.dict()
    # Insert the data into MongoDB
    result = await collection.insert_one(document)
    
    if result.inserted_id:
        return {"status": "success", "message": "Data saved to MongoDB", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to save data")

@app.get("/api/latest")
async def get_latest_data():
    """Endpoint to get the most recent sensor reading."""
    document = await collection.find_one(sort=[("_id", -1)])
    if document:
        document["_id"] = str(document["_id"])
        return document
    return {"message": "No data available"}

@app.get("/api/history", response_model=List[dict])
async def get_history(limit: int = 10):
    """Endpoint to get historical sensor readings."""
    cursor = collection.find().sort("_id", -1).limit(limit)
    history = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        history.append(document)
    return history

@app.get("/")
async def root():
    return {"message": "Smart Dustbin API is running. ESP32 should POST to /api/data"}