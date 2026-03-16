import requests
import random
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/data"

CATEGORIES = ["Metal", "Plastic", "Other"]

def simulate_reading():
    category = random.choice(CATEGORIES)
    distance = round(random.uniform(5.0, 30.0), 2)
    
    # Simple logic: closer to sensor = fuller bin
    # Assume bin depth is 30cm. Distance 5cm means 83% full. Distance 30cm means 0% full.
    fill_percentage = max(0, min(100, round((30 - distance) / 25 * 100, 2)))
    
    data = {
        "ultrasonic_distance": distance,
        "inductive": 1 if category == "Metal" else 0,
        "capacitive": 1 if category == "Plastic" else 0,
        "waste_category": category,
        "fill_percentage": fill_percentage,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent: {category} | {fill_percentage}% Full | Dist: {distance}cm")
        else:
            print(f"Failed to send data: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting ESP32 Simulation... (Press Ctrl+C to stop)")
    while True:
        simulate_reading()
        time.sleep(3) # Send every 3 seconds
