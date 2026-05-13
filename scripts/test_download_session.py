import asyncio
import os
import json
import urllib.parse
from pytapo import Tapo
from pytapo.media_stream._utils import StreamType
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

# Global Tapo object
tapo = None

async def download_chunks(start_time, device_id):
    global tapo
    session = tapo.getMediaSession(StreamType.Download, start_time=str(start_time))
    
    # Manually setting query_params with device_id
    session.query_params = {
        "deviceId": device_id,
        "playerId": tapo.playerID,
        "type": "sdvod",
        "start_time": str(start_time),
    }
    # Re-generate the query string
    session.query_params_str = f"?{urllib.parse.urlencode(session.query_params)}"

    print(f"Starting media session with params: {session.query_params_str}")
    
    try:
        async with session:
            # We need to send a request to start the playback
            request_data = json.dumps({
                "type": "request",
                "seq": 1,
                "method": "get",
                "params": {
                    "session_id": "0"
                }
            })
            
            count = 0
            # Increase timeout to 30s
            async for response in session.transceive(request_data, encrypt=True, no_data_timeout=30.0):
                print(f"Received chunk {count+1}: {len(response.plaintext)} bytes, type: {response.mimetype}")
                count += 1
                if count >= 3:
                    break
            
            if count > 0:
                print("Download test successful!")
            else:
                print("No data received.")
            
    except Exception as e:
        print(f"Error during download: {e}")

def main():
    global tapo
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    cloud_pass = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, cloud_pass]):
        print("Error: Missing credentials in .env file.")
        return

    tapo = Tapo(ip, email, cloud_pass, cloudPassword=cloud_pass)
    
    # Get dev_id from basic info
    info = tapo.getBasicInfo()
    device_id = info['device_info']['basic_info']['dev_id']
    
    dates_raw = tapo.getRecordingsList()
    dates = []
    for item in dates_raw:
        for key in item:
            if 'date' in item[key]:
                dates.append(item[key]['date'])
    
    latest_date = sorted(dates)[-1]
    clips_raw = tapo.getRecordings(latest_date)
    clips = []
    for item in clips_raw:
        for key in item:
            clips.append(item[key])
    
    clips.sort(key=lambda x: x['startTime'], reverse=True)
    start_time = clips[0]['startTime']
    
    print(f"Found latest clip starting at {start_time} for device {device_id}")
    
    asyncio.run(download_chunks(start_time, device_id))

if __name__ == "__main__":
    main()
