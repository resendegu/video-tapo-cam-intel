import os
from pytapo import Tapo
import inspect
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def inspect_recording_methods():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    password = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, password]):
        print("Error: Missing credentials in .env file.")
        return

    tapo = Tapo(ip, email, password)
    
    for method_name in ['getRecordings', 'getRecordingsList', 'getRecordingsUTC']:
        method = getattr(tapo, method_name)
        print(f"\n--- {method_name} ---")
        try:
            print(f"Signature: {inspect.signature(method)}")
        except:
            print("Could not get signature")

if __name__ == "__main__":
    inspect_recording_methods()
