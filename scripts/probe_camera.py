import asyncio
from onvif2 import ONVIFCamera
import sys
import os
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

def probe_camera():
    ip = os.getenv('TAPO_IP')
    port = 2020
    user = os.getenv('ONVIF_USER')
    password = os.getenv('ONVIF_PASS')
    
    if not all([ip, user, password]):
        print("Error: Missing ONVIF credentials in .env file.")
        return
    print(f"Connecting to camera at {ip}:{port}...")
    try:
        # Create the camera object
        mycam = ONVIFCamera(ip, port, user, password)
        
        # Get Device Information
        try:
            resp = mycam.devicemgmt.GetDeviceInformation()
            print("\n--- Device Information ---")
            print(f"Manufacturer: {resp.Manufacturer}")
            print(f"Model: {resp.Model}")
            print(f"Firmware Version: {resp.FirmwareVersion}")
            print(f"Serial Number: {resp.SerialNumber}")
            print(f"Hardware Id: {resp.HardwareId}")
        except Exception as e:
            print(f"Error getting Device Information: {e}")

        # Get Services
        print("\n--- Services ---")
        try:
            services = mycam.devicemgmt.GetServices({'IncludeCapability': True})
            for s in services:
                print(f"Service: {s.Namespace} at {s.XAddr}")
        except Exception as e:
            print(f"Error getting Services: {e}")

        # Get Capabilities
        print("\n--- Capabilities ---")
        try:
            capabilities = mycam.devicemgmt.GetCapabilities({'Category': 'All'})
            print(f"Media: {capabilities.Media.XAddr if (capabilities.Media and hasattr(capabilities.Media, 'XAddr')) else 'Not Supported'}")
            print(f"PTZ: {capabilities.PTZ.XAddr if (capabilities.PTZ and hasattr(capabilities.PTZ, 'XAddr')) else 'Not Supported'}")
            print(f"Imaging: {capabilities.Imaging.XAddr if (capabilities.Imaging and hasattr(capabilities.Imaging, 'XAddr')) else 'Not Supported'}")
            print(f"Events: {capabilities.Events.XAddr if (capabilities.Events and hasattr(capabilities.Events, 'XAddr')) else 'Not Supported'}")
        except Exception as e:
            print(f"Error getting Capabilities: {e}")

        # Media Profiles
        print("\n--- Media Profiles ---")
        try:
            media_service = mycam.create_media_service()
            profiles = media_service.GetProfiles()
            for profile in profiles:
                print(f"Profile Name: {profile.Name} (Token: {profile.token})")
                
                # Get Stream URI
                stream_setup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
                try:
                    uri = media_service.GetStreamUri({'StreamSetup': stream_setup, 'ProfileToken': profile.token})
                    print(f"  Stream URI: {uri.Uri}")
                except Exception as e:
                    print(f"  Error getting stream URI: {e}")
        except Exception as e:
            print(f"Error getting Media Profiles: {e}")

        # Replay Service (SD Card)
        print("\n--- Replay / Recording Services ---")
        try:
            replay_service = mycam.create_replay_service()
            print("Replay Service IS available!")
            try:
                # Try to get replay URI for the first profile
                if profiles:
                    replay_uri = replay_service.GetReplayStreamUri({
                        'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}},
                        'RecordingToken': profiles[0].token # Just a guess for token
                    })
                    print(f"  Replay URI: {replay_uri.Uri}")
            except Exception as e:
                print(f"  Error getting Replay URI: {e}")
        except Exception:
            print("Replay Service is NOT available.")

        try:
            search_service = mycam.create_search_service()
            print("Search Service IS available!")
        except Exception:
            print("Search Service is NOT available.")

    except Exception as e:
        print(f"Error connecting to camera: {e}")

if __name__ == "__main__":
    probe_camera()
