import os
from pytapo import Tapo
import inspect
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def inspect_tapo():
    ip = os.getenv('TAPO_IP')
    email = os.getenv('TAPO_EMAIL')
    password = os.getenv('TAPO_CLOUD_PASS')
    
    if not all([ip, email, password]):
        print("Error: Missing credentials in .env file.")
        return

    tapo = Tapo(ip, email, password)
    print("\n--- Available Methods in Tapo Class ---")
    methods = [m for m, _ in inspect.getmembers(tapo, predicate=inspect.ismethod)]
    for m in sorted(methods):
        print(m)

if __name__ == "__main__":
    inspect_tapo()
