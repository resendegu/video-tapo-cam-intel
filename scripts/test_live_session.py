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

async def test_live(device_id):
    global tapo
    session = tapo.getMediaSession(StreamType.Stream)
    session.query_params = {
        "deviceId": device_id,
        "playerId": tapo.playerID,
        "type": "video",
    }
    session.query_params_str = f"?{urllib.parse.urlencode(session.query_params)}"

    print(f"Starting LIVE media session with params: {session.query_params_str}")
    
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
            async for response in session.transceive(request_data, encrypt=True, no_data_timeout=10.0):
                print(f"Received LIVE chunk {count+1}: {len(response.plaintext)} bytes, mimetype: {response.mimetype}")
                count += 1
                if count >= 3:
                    break
            
            if count > 0:
                print("LIVE stream test successful!")
    except Exception as e:
        print(f"Error: {e}")

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
    
    asyncio.run(test_live(device_id))

if __name__ == "__main__":
    main()
