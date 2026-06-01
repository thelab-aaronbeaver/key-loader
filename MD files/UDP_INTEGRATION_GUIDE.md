# UDP LightBurn Integration Guide

## Overview

The Flask app now sends UDP triggers to LightBurn **in addition to** triggering the Raspberry Pico. When a key is detected during the cycle, both triggers fire simultaneously.

## How It Works

```
Key Detected
    ↓
┌───────────────────────────────────┐
│  send_pico_command()              │
│  ├─► Trigger Pico (GPIO pulse)    │
│  └─► send_udp_trigger()           │
│       └─► UDP to LightBurn        │
└───────────────────────────────────┘
```

## Configuration

### Config File (`config.json`)

New UDP settings have been added:

```json
{
  "udp_enabled": true,         // Enable/disable UDP trigger
  "udp_ip": "127.0.0.1",       // Target IP (localhost or remote machine)
  "udp_port": 5005,            // UDP port number
  "udp_message": "START"       // Trigger message to send
}
```

### Settings Explained:

- **`udp_enabled`**: Set to `false` to disable UDP (only Pico will trigger)
- **`udp_ip`**: 
  - `127.0.0.1` = Same machine (LightBurn on same Raspberry Pi)
  - `192.168.1.100` = Remote machine on network
- **`udp_port`**: Must match the listener port (default: 5005)
- **`udp_message`**: Must match what listener expects (default: "START")

## Setup Instructions

### Option 1: LightBurn on Same Machine

1. **Update config.json:**
   ```json
   {
     "udp_enabled": true,
     "udp_ip": "127.0.0.1",
     "udp_port": 5005,
     "udp_message": "START"
   }
   ```

2. **Run the improved listener:**
   ```bash
   python3 lazer_trigger_improved.py
   ```

3. **Test it from config page:**
   - Open Configuration page
   - Click "Test UDP Trigger" button (you'll need to add this to UI)

### Option 2: LightBurn on Different Machine

1. **Find the IP of the LightBurn machine:**
   ```bash
   # On the LightBurn machine:
   ifconfig  # Linux/Mac
   ipconfig  # Windows
   ```

2. **Update config.json with that IP:**
   ```json
   {
     "udp_enabled": true,
     "udp_ip": "192.168.1.100",  // Replace with actual IP
     "udp_port": 5005,
     "udp_message": "START"
   }
   ```

3. **Run listener on LightBurn machine:**
   ```bash
   python3 lazer_trigger_improved.py
   ```

## Testing

### Test UDP Trigger via API

```bash
# Test UDP trigger
curl -X POST http://localhost:5000/api/udp/test
```

### Test Complete System

```bash
# Test both Pico and UDP
curl -X POST http://localhost:5000/api/pico/test
```

## Console Output

When working correctly, you'll see in the Flask console:

```
📡 Sending to Pico: keyboard_enter (emulating keyboard Enter press)
📡 UDP trigger sent to 127.0.0.1:5005 - Message: 'START'
```

If UDP is disabled:
```
📡 Sending to Pico: keyboard_enter (emulating keyboard Enter press)
⏭️  UDP trigger disabled in config
```

If UDP fails:
```
📡 Sending to Pico: keyboard_enter (emulating keyboard Enter press)
❌ UDP trigger error: [Errno 111] Connection refused
```

## Listener Output

In the `lazer_trigger_improved.py` console:

```
📨 Received message 'START' from 127.0.0.1:52341
🎯 Trigger detected! Sending Enter key to LightBurn...
✅ Successfully sent Enter key to LightBurn
```

## Troubleshooting

### UDP Not Working

1. **Check listener is running:**
   ```bash
   ps aux | grep lazer_trigger
   ```

2. **Check port is listening:**
   ```bash
   netstat -ulnp | grep 5005
   ```

3. **Test with manual UDP send:**
   ```bash
   echo "START" | nc -u localhost 5005
   ```

4. **Check firewall:**
   ```bash
   # Linux
   sudo ufw allow 5005/udp
   
   # Windows
   # Add inbound rule for UDP port 5005
   ```

### Pico Not Working

- Check GPIO 4 wiring
- Check Pico is running the MicroPython script
- Test with `/api/pico/test` endpoint

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/udp/test` | POST | Test UDP trigger only |
| `/api/pico/test` | POST | Test both Pico and UDP |
| `/api/config` | GET | Get config (includes UDP settings) |
| `/api/config` | POST | Update config (includes UDP settings) |

## Platform Compatibility

- **UDP Sender (Flask app)**: ✅ Works on any platform (Windows/Linux/macOS)
- **UDP Listener (`lazer_trigger_improved.py`)**: ⚠️ macOS only (uses AppleScript)

### For Windows/Linux LightBurn:

You'll need to modify `lazer_trigger_improved.py` to use platform-specific keyboard input methods:

- **Windows**: Use `pyautogui` or `keyboard` library
- **Linux**: Use `xdotool` or `pyautogui`

Example for cross-platform:

```python
import platform
import pyautogui  # pip install pyautogui

def send_keystroke_crossplatform():
    pyautogui.press('enter')
```

## Log Files

- **Flask app**: Check terminal output
- **UDP listener**: Check `lazer_trigger.log`

## Disable UDP Temporarily

Set in `config.json`:
```json
{
  "udp_enabled": false
}
```

Restart Flask app or save via `/api/config` endpoint.

