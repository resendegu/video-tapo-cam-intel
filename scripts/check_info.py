import os
import json
from pytapo import Tapo
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def check_basic_info():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    cloud_pass = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, cloud_pass]):
        print("Error: Missing credentials in .env file.")
        return

    tapo = Tapo(ip, email, cloud_pass, cloudPassword=cloud_pass)
    info = tapo.getBasicInfo()
    print(json.dumps(info, indent=2))

if __name__ == "__main__":
    check_basic_info()
