# Exploring Tapo C500 Capabilities

This document summarizes the research and experiments conducted to interface with the Tapo C500 IP camera using standard (ONVIF) and proprietary protocols.

## Key Findings

### 1. Protocols & Connectivity
*   **ONVIF (Port 2020)**: The camera supports ONVIF v2.0. This is the primary method for device discovery, system information, and standard PTZ control.
*   **RTSP (Port 554)**: Standard RTSP streaming is available for live video feeds.
    *   `rtsp://user:pass@ip:554/stream1` (1080p Main Stream)
    *   `rtsp://user:pass@ip:554/stream2` (Minor Stream)
*   **Proprietary Control (Port 443/8800)**: Used for advanced features like SD card recording management and cloud-synced settings. This requires the `pytapo` library.

### 2. PTZ (Pan-Tilt-Zoom)
*   The camera supports full PTZ control via ONVIF.
*   Capabilities include Continuous, Absolute, and Relative movement.
*   A "Calibrate" command is also available via the proprietary protocol to reset the motor positions.

### 3. SD Card Recording Access
*   **ONVIF Limitation**: Standard ONVIF Replay/Recording services are **not** fully exposed or functional for SD card retrieval on this model.
*   **Solution**: Use the `pytapo` library which interacts with the proprietary Tapo API.
    *   We can list recorded dates and specific clips (start/end timestamps).
    *   **Downloading** recordings requires a media session on port 8800 and the Tapo Cloud password for decryption.
    *   **Requirement**: FFmpeg is required to process and reassemble the encrypted stream chunks into video files.

---

## Modules Used

*   `onvif2-zeep`: Synchronous ONVIF client library.
*   `pytapo`: Unofficial library for Tapo-specific features (Cloud sync, SD card, privacy mode).
*   `opencv-python-headless`: Used for testing RTSP stream connectivity and frame capture.
*   `python-dotenv`: For managing sensitive credentials securely.

---

## Workspace Organization

All research and debugging scripts have been moved to the `scripts/` directory to keep the root clean for the final application.

### Scripts in `scripts/`

| Script | Purpose |
| :--- | :--- |
| `probe_camera.py` | Probes ONVIF services (Media, PTZ, Imaging) and lists RTSP endpoints. |
| `probe_ptz.py` | Detailed inspection of PTZ nodes and supported movement spaces. |
| `test_stream.py` | Verifies live RTSP streaming using OpenCV. |
| `list_all_recordings.py` | Lists all dates and individual clips available on the SD card. |
| `check_info.py` | Retrieves detailed device info (MAC, Device ID, Firmware) via Tapo API. |
| `inspect_tapo.py` | Utility to list all available methods in the `pytapo` library for debugging. |
| `test_auth.py` | Verifies different credential combinations (Camera Account vs Cloud). |
| `test_live_session.py` | Tests the proprietary media stream session for live video. |
| `test_download_session.py` | Research into downloading encrypted .ts chunks from the SD card. |

---

## Security

*   Credentials are now stored in a `.env` file (not committed to version control).
*   A `.env.example` file is provided as a template.
*   Scripts have been updated to load variables using `python-dotenv`.

## Future Work
*   Integrate FFmpeg into the download pipeline.
*   Develop a consolidated application for automated recording retrieval and storage.
