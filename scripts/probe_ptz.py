import os
from onvif2 import ONVIFCamera
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def probe_ptz():
    ip = os.getenv('TAPO_IP')
    port = 2020
    user = os.getenv('ONVIF_USER')
    password = os.getenv('ONVIF_PASS')
    
    if not all([ip, user, password]):
        print("Error: Missing ONVIF credentials in .env file.")
        return

    print(f"Connecting to camera for PTZ probe...")
    try:
        mycam = ONVIFCamera(ip, port, user, password)
        ptz = mycam.create_ptz_service()
        
        # Get PTZ Configurations
        configs = ptz.GetConfigurations()
        print("\n--- PTZ Configurations ---")
        for config in configs:
            print(f"Name: {config.Name}")
            print(f"Node Token: {config.NodeToken}")
            
        # Get Nodes
        nodes = ptz.GetNodes()
        print("\n--- PTZ Nodes ---")
        for node in nodes:
            print(f"Node: {node.Name} (Token: {node.token})")
            print(f"  Supported Spaces:")
            if hasattr(node, 'SupportedPTZSpaces'):
                s = node.SupportedPTZSpaces
                print(f"    Continuous Pan/Tilt: {hasattr(s, 'ContinuousPanTiltVelocitySpace')}")
                print(f"    Continuous Zoom: {hasattr(s, 'ContinuousZoomVelocitySpace')}")
                print(f"    Absolute Pan/Tilt: {hasattr(s, 'AbsolutePanTiltPositionSpace')}")
                print(f"    Relative Pan/Tilt: {hasattr(s, 'RelativePanTiltTranslationSpace')}")

    except Exception as e:
        print(f"Error probing PTZ: {e}")

if __name__ == "__main__":
    probe_ptz()
