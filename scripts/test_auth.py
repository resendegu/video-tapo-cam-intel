import os
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def test_auth():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    cloud_pass = os.getenv('TAPO_CLOUD_PASS')
    cam_user = os.getenv('ONVIF_USER')
    cam_pass = os.getenv('ONVIF_PASS')
    
    if not all([ip, email, cloud_pass, cam_user, cam_pass]):
        print("Error: Missing credentials in .env file.")
        return

    combinations = [
        ("Cloud Email + Cloud Pass", email, cloud_pass),
        ("Admin + Cloud Pass", "admin", cloud_pass),
        ("Cam User + Cam Pass", cam_user, cam_pass),
        ("Cam User + Cloud Pass", cam_user, cloud_pass),
    ]
    
    for label, u, p in combinations:
        print(f"Testing {label}...")
        try:
            tapo = Tapo(ip, u, p, cloudPassword=cloud_pass)
            print(f"  SUCCESS: {label}")
            return # Stop at first success
        except Exception as e:
            print(f"  FAILED: {label} - {e}")

if __name__ == "__main__":
    test_auth()
