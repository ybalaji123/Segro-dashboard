"""
Smart Segro — Polling Worker
─────────────────────────────
This script runs in the background on the laptop.
It continuously polls the ESP32 (which is acting as an Access Point)
at http://192.168.4.1/data.

When a new waste item is documented (based on reading ID), this
script forwards it to the FastAPI backend to store in MongoDB and
serve to the dashboard.
"""

import requests
import time
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────
# 1. Look at your ESP32's display/serial monitor to find its IP.
# 2. Type it here. (e.g., http://192.168.43.14/data)
ESP32_URL = "http://192.168.X.X/data"

BACKEND_URL = "http://localhost:8080/api/sensor-data"

# Keeps track of the last processed ID to prevent duplicates
last_processed_id = 0

def poll_and_forward():
    global last_processed_id

    try:
        # 1. Fetch data from ESP32
        # Timeout of 2s because if we are not connected to ESP32 Wi-Fi, it will hang.
        esp_response = requests.get(ESP32_URL, timeout=2)
        
        if esp_response.status_code == 200:
            data = esp_response.json()
            current_id = data.get("id", 0)

            # If the ID has increased, it means a new item was dropped
            if current_id > last_processed_id:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] NEW DATA >> {data['waste_type']} ({data['status']})")
                
                # Forward to our FastAPI backend
                payload = {
                    "waste_type": data.get("waste_type", "Unknown"),
                    "status": data.get("status", "Collected")
                }

                try:
                    backend_resp = requests.post(BACKEND_URL, json=payload, timeout=2)
                    if backend_resp.status_code == 200:
                        print("  [OK] Saved to MongoDB via FastAPI.")
                        last_processed_id = current_id
                    else:
                        print(f"  [ERR] Backend Error: {backend_resp.status_code}")
                except requests.ConnectionError:
                    print("  [ERR] Could not reach FastAPI Backend. Is it running on localhost:8080?")
                    
            else:
                # Same ID or 0, do nothing
                pass
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ESP32 returned HTTP {esp_response.status_code}")

    except requests.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Cannot reach ESP32 at {ESP32_URL}. Are you connected to SmartSegro_WiFi?")
    except requests.Timeout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Timeout reaching ESP32.")
    except Exception as e:
        pass


if __name__ == "__main__":
    print(f"=================================================")
    print(f" Smart Segro ESP32 Poller Started")
    print(f" Target: {ESP32_URL}")
    print(f" Destination: {BACKEND_URL}")
    print(f"=================================================\n")
    
    while True:
        poll_and_forward()
        time.sleep(1) # Poll every 1 second
