import os
import json
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def list_clips_raw():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    password = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, password]):
        print("Error: Missing credentials in .env file.")
        return

    tapo = Tapo(ip, email, password)
    dates_raw = tapo.getRecordingsList()
    dates = []
    for item in dates_raw:
        for key in item:
            if 'date' in item[key]:
                dates.append(item[key]['date'])
    
    if not dates:
        print("No recordings found.")
        return

    latest_date = sorted(dates)[-1]
    clips = tapo.getRecordings(latest_date)
    
    print(f"Latest Date: {latest_date}")
    print(f"Total Clips: {len(clips)}")
    if clips:
        print("\nRaw data for the first clip:")
        print(json.dumps(clips[0], indent=2))

if __name__ == "__main__":
    list_clips_raw()
