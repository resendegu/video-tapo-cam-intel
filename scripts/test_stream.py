import cv2
import time
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def test_stream():
    # Credentials and IP from user
    user = os.getenv('ONVIF_USER')
    password = os.getenv('ONVIF_PASS')
    ip = os.getenv('TAPO_IP')
    
    if not all([ip, user, password]):
        print("Error: Missing ONVIF credentials in .env file.")
        return

    # Try the main stream URL found via ONVIF
    rtsp_url = f"rtsp://{user}:{password}@{ip}:554/stream1"
    
    print(f"Connecting to RTSP stream: {rtsp_url.replace(password, '********')}")
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    # Get some properties
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Stream Properties: {int(width)}x{int(height)} @ {fps} FPS")

    # Read a few frames to verify
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"Successfully read frame {i+1}")
        else:
            print(f"Failed to read frame {i+1}")
        time.sleep(0.1)

    cap.release()
    print("Test completed.")

if __name__ == "__main__":
    test_stream()
