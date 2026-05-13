import asyncio
import os
import json
import urllib.parse
from pytapo import Tapo
from pytapo.media_stream._utils import StreamType
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

tapo = None

async def test_download_hack(device_id, start_time):
    global tapo
    # HACK: Set childID to device_id to trick getMediaSession
    tapo.childID = device_id
    session = tapo.getMediaSession(StreamType.Download, start_time=str(start_time))
    
    print(f"Session query params: {session.query_params}")
    
    try:
        async with session:
            request_data = json.dumps({
                "type": "request",
                "seq": 1,
                "method": "get",
                "params": {
                    "session_id": "0"
                }
            })
            
            count = 0
            async for response in session.transceive(request_data, encrypt=True, no_data_timeout=15.0):
                print(f"Received chunk {count+1}: {len(response.plaintext)} bytes")
                count += 1
                if count >= 3:
                    break
            
            if count > 0:
                print("HACK SUCCESSFUL!")
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
    info = tapo.getBasicInfo()
    device_id = info['device_info']['basic_info']['dev_id']
    
    dates_raw = tapo.getRecordingsList()
    latest_date = sorted([item[key]['date'] for item in dates_raw for key in item])[-1]
    clips_raw = tapo.getRecordings(latest_date)
    clips = [item[key] for item in clips_raw for key in item]
    clips.sort(key=lambda x: x['startTime'], reverse=True)
    start_time = clips[0]['startTime']
    
    print(f"Testing hack for clip {start_time} on device {device_id}...")
    
    asyncio.run(test_download_hack(device_id, start_time))

if __name__ == "__main__":
    main()
