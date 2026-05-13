import os
import json
from datetime import datetime
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def list_clips():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    password = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, password]):
        print("Error: Missing credentials in .env file.")
        return

    print(f"Connecting to Tapo camera at {ip}...")
    try:
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
        print(f"\nFetching clips for latest date: {latest_date}...")
        
        clips_raw = tapo.getRecordings(latest_date)
        
        print("\n--- Clips Found (Most Recent 10) ---")
        clips = []
        for item in clips_raw:
            for key in item:
                clip_data = item[key]
                clips.append({
                    'start': clip_data.get('startTime'),
                    'end': clip_data.get('endTime'),
                    'type': clip_data.get('vedio_type')
                })
        
        # Sort by start time descending
        clips.sort(key=lambda x: x['start'], reverse=True)
        
        for i, clip in enumerate(clips[:10]):
            start_dt = datetime.fromtimestamp(clip['start'])
            end_dt = datetime.fromtimestamp(clip['end'])
            duration = clip['end'] - clip['start']
            print(f"Clip {i+1}: {start_dt.strftime('%H:%M:%S')} - {end_dt.strftime('%H:%M:%S')} ({duration}s) Type: {clip['type']}")

        if clips:
            target = clips[0]
            print(f"\nGetting playback metadata for the most recent clip ({datetime.fromtimestamp(target['start']).strftime('%H:%M:%S')})...")
            
            print(f"Using getRecordingsUTC({target['start']}, {target['end']})...")
            playback_data = tapo.getRecordingsUTC(target['start'], target['end'])
            print("\n--- Playback Metadata ---")
            print(json.dumps(playback_data, indent=2))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_clips()
