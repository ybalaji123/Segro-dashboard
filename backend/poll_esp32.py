"""
Smart Segro — Polling Worker (HTML SCAPER VERSION)
─────────────────────────────
This script runs in the background on the laptop.
It continuously polls the ESP32 (which is connected to the same Phone Hotspot as the laptop)
at http://<ESP32_IP>/data.

Since the ESP32 is currently returning HTML instead of JSON, we scrape the HTML.
When a new waste item is documented (changing from 'None' to something else), 
this script forwards it to the FastAPI/Render backend to store in MongoDB and
serve to the dashboard.
"""

import requests
import time
import re
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────
ESP32_URL = "http://192.168.137.56/"
BACKEND_URL = "https://segro-dashboard.onrender.com/api/sensor-data"

# Keeps track of the last waste state to prevent spamming
last_waste_state = "None"

def poll_and_forward():
    global last_waste_state

    try:
        # 1. Fetch HTML from ESP32
        esp_response = requests.get(ESP32_URL, timeout=2)
        
        if esp_response.status_code == 200:
            text = esp_response.text
            
            # Scrape HTML: <h2>Waste Type: None</h2>
            waste_match = re.search(r'<h2>Waste Type:\s*(.*?)</h2>', text)
            # Scrape HTML: <h2>Status: Waiting</h2>
            status_match = re.search(r'<h2>Status:\s*(.*?)</h2>', text)
            
            current_waste = waste_match.group(1) if waste_match else "None"
            current_status = status_match.group(1) if status_match else "Waiting"

            # If waste type changed from None to something like "Metal" or "Plastic"
            if current_waste != "None" and current_waste != last_waste_state:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] NEW DATA >> {current_waste} ({current_status})")
                
                # Forward to our FastAPI backend on Render
                payload = {
                    "waste_type": current_waste,
                    "status": current_status
                }

                try:
                    backend_resp = requests.post(BACKEND_URL, json=payload, timeout=5)
                    if backend_resp.status_code == 200:
                        print("  [OK] Saved to MongoDB via API.")
                    else:
                        print(f"  [ERR] Backend Error: {backend_resp.status_code}")
                except requests.ConnectionError:
                    print("  [ERR] Could not reach Backend.")
                
            # Update last state so we don't send duplicates
            last_waste_state = current_waste
            
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ESP32 returned HTTP {esp_response.status_code}")

    except requests.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Cannot reach ESP32 at {ESP32_URL}. Are you on the SAME hotspot network, and is the IP correct?")
    except requests.Timeout:
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Timeout reaching ESP32.")
        pass
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERR] Unexpected error: {e}")

if __name__ == "__main__":
    print(f"=================================================")
    print(f" Smart Segro ESP32 Poller Started (HTML Version)")
    print(f" Target: {ESP32_URL}")
    print(f" Destination: {BACKEND_URL}")
    print(f"=================================================\n")
    
    while True:
        poll_and_forward()
        time.sleep(1) # Poll every 1 second
