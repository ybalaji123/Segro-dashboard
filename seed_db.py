import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def seed_database():
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("Error: MONGODB_URI not found in .env file.")
        return

    try:
        client = MongoClient(mongo_uri)
        db = client.smart_dustbin
        collection = db.sensor_readings

        print(f"Connecting to MongoDB...")

        categories = ["Metal", "Plastic", "Other"]
        records = []

        # Generate some historical data for the last 2 hours
        now = datetime.now()
        for i in range(15):
            category = random.choice(categories)
            distance = round(random.uniform(5.0, 25.0), 2)
            fill_percentage = max(0, min(100, round((30 - distance) / 25 * 100, 2)))
            
            timestamp = now - timedelta(minutes=random.randint(1, 120))
            
            record = {
                "ultrasonic_distance": distance,
                "inductive": 1 if category == "Metal" else 0,
                "capacitive": 1 if category == "Plastic" else 0,
                "waste_category": category,
                "fill_percentage": fill_percentage,
                "timestamp": timestamp
            }
            records.append(record)

        # Insert records
        if records:
            result = collection.insert_many(records)
            print(f"Successfully inserted {len(result.inserted_ids)} records into MongoDB.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    seed_database()
