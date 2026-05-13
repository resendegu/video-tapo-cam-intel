import os
import json
from datetime import datetime
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def list_recordings():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    password = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, password]):
        print("Error: Missing credentials in .env file.")
        return

    print(f"Connecting to Tapo camera at {ip} with cloud account {email}...")
    try:
        tapo = Tapo(ip, email, password)
        
        print("\nFetching all recordings (this might take a moment)...")
        # getRecordingsList without arguments uses default start_date='20000101'
        recordings = tapo.getRecordingsList()
        
        print("\n--- Recordings Found ---")
        if not recordings:
            print("No recordings found on the SD card.")
        else:
            print(f"Total recordings: {len(recordings)}")
            print("\nFirst 5 recordings:")
            print(json.dumps(recordings[:5], indent=2))
            
            # Group by date
            dates = set()
            for r in recordings:
                for key in r:
                    if 'date' in r[key]:
                        dates.add(r[key]['date'])
            
            if dates:
                print(f"\nRecorded dates: {sorted(list(dates))}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_recordings()
