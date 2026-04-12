"""
ESP32 Simulator
───────────────
Sends simulated waste detection events to the FastAPI backend
at POST /api/sensor-data every 3 seconds, mimicking what the
real ESP32 does over the mobile hotspot LAN.

Usage:
    python simulate_esp32.py              # defaults to localhost:8000
    python simulate_esp32.py 192.168.1.5  # specify laptop IP manually
"""

import requests
import random
import sys
import time
from datetime import datetime

# Accept optional IP as CLI arg (for testing on mobile hotspot)
HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
API_URL = f"http://{HOST}:8080/api/sensor-data"

WASTE_TYPES = ["Metal", "Plastic"]
STATUSES    = ["Collected"]  # extend later if needed


def simulate_reading():
    waste = random.choice(WASTE_TYPES)
    status = random.choice(STATUSES)

    payload = {
        "waste_type": waste,
        "status":     status,
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=5)
        ts = datetime.now().strftime("%H:%M:%S")
        if resp.status_code == 200:
            print(f"[{ts}] [OK]  Sent: {waste} - {status}")
        else:
            print(f"[{ts}] [ERR] HTTP {resp.status_code}: {resp.text}")
    except requests.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Cannot reach {API_URL}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARN] Error: {e}")


if __name__ == "__main__":
    print(f"[~] ESP32 Simulator -> {API_URL}")
    print("   Press Ctrl+C to stop\n")
    while True:
        simulate_reading()
        time.sleep(3)
