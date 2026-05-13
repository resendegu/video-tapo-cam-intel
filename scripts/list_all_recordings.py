import os
import json
from datetime import datetime
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def main():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    cloud_pass = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, cloud_pass]):
        print("Error: Missing credentials in .env file. Please check .env.example.")
        return

    print(f"--- Tapo C500 Recording Explorer ---")
    print(f"Connecting to camera at {ip}...")
    
    try:
        # Initialize Tapo with cloud credentials
        tapo = Tapo(ip, email, cloud_pass, cloudPassword=cloud_pass)
        
        print("Fetching recorded dates...")
        dates_raw = tapo.getRecordingsList()
        
        dates = []
        for item in dates_raw:
            for key in item:
                if 'date' in item[key]:
                    dates.append(item[key]['date'])
        
        if not dates:
            print("No recordings found on the SD card.")
            return
            
        print(f"Found {len(dates)} days with recordings: {', '.join(sorted(dates))}")
        
        # Get clips for today
        today = datetime.now().strftime("%Y%m%d")
        if today not in dates:
            print(f"No recordings for today ({today}). Showing clips for the most recent date instead.")
            target_date = sorted(dates)[-1]
        else:
            target_date = today
            
        print(f"\n--- Clips for {target_date} ---")
        clips_raw = tapo.getRecordings(target_date)
        
        clips = []
        for item in clips_raw:
            for key in item:
                clip_data = item[key]
                clips.append({
                    'start': clip_data.get('startTime'),
                    'end': clip_data.get('endTime'),
                    'type': clip_data.get('vedio_type')
                })
        
        # Sort by start time descending (most recent first)
        clips.sort(key=lambda x: x['start'], reverse=True)
        
        print(f"{'Start Time':<15} | {'Duration':<10} | {'Type'}")
        print("-" * 40)
        for clip in clips[:20]: # Show last 20 clips
            start_dt = datetime.fromtimestamp(clip['start'])
            duration = clip['end'] - clip['start']
            ctype = "Motion" if clip['type'] == '2' or clip['type'] == 2 else f"Other ({clip['type']})"
            print(f"{start_dt.strftime('%H:%M:%S'):<15} | {duration:<10}s | {ctype}")
            
        if len(clips) > 20:
            print(f"... and {len(clips) - 20} more clips.")

        print("\n[Status] Connection successful. SD Card contents accessible.")
        print("[Next Step] To download these clips, FFmpeg needs to be installed on the system.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
