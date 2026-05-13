import os
import json
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def probe_tapo():
    ip = os.getenv('TAPO_IP')
    user = os.getenv('ONVIF_USER')
    password = os.getenv('ONVIF_PASS')
    
    if not all([ip, user, password]):
        print("Error: Missing credentials in .env file.")
        return

    print(f"Connecting to Tapo camera at {ip}...")
    try:
        tapo = Tapo(ip, user, password)
        
        # Get basic info
        device_info = tapo.getBasicInfo()
        print("\n--- Device Information ---")
        print(json.dumps(device_info, indent=2))
        
    except Exception as e:
        print(f"Error connecting to camera: {e}")

if __name__ == "__main__":
    probe_tapo()
