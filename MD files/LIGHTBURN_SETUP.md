# LightBurn Integration Setup Guide

This guide explains how to set up LightBurn on your Mac to work with the key-loader automation system.

## Overview

The key-loader system now integrates with LightBurn via UDP automation. Instead of using a fixed pause timer, the system:

1. **Starts LightBurn jobs** via UDP command (START)
2. **Monitors job status** by polling LightBurn (STATUS command)
3. **Waits for job completion** before proceeding to next key

This eliminates the need for manual timing and ensures perfect synchronization.

## LightBurn UDP Automation Setup (Mac)

### Step 1: Enable UDP in LightBurn

1. Open **LightBurn** on your Mac
2. Go to **Edit** → **Device Settings**
3. Look for **"Enable UDP Listening"** or **"Network API"** option
4. Enable it and note the ports:
   - **Outgoing Port**: 19840 (default - where LightBurn receives commands)
   - **Incoming Port**: 19841 (default - where LightBurn sends responses)

### Step 2: Configure Network Settings

1. Find your Mac's IP address:
   - Open **System Preferences** → **Network**
   - Note the IP address (should be `192.168.1.170` based on your current config)

2. Ensure your Mac and Raspberry Pi are on the same network

3. Check firewall settings (if enabled):
   - Go to **System Preferences** → **Security & Privacy** → **Firewall**
   - Click **Firewall Options**
   - Ensure LightBurn is allowed to receive incoming connections
   - Allow incoming connections on ports 19840 and 19841

### Step 3: Test the Connection

1. Start LightBurn on your Mac
2. Load a test project/file in LightBurn
3. On the key-loader web interface, go to **Configuration** page
4. In the **LightBurn Integration** section:
   - Click **"Test Connection"** - should show "Connected" if working
   - Click **"Get Status"** - should show LightBurn's current status (IDLE or BUSY)
   - Click **"Start Job"** - should start the loaded job (test carefully!)

## Configuration Settings

The system can be configured via the **Configuration** page or by editing `config.json`:

### LightBurn Settings in `config.json`

```json
{
  "lightburn_enabled": true,          // Enable/disable LightBurn integration
  "lightburn_ip": "192.168.1.170",    // Mac IP address
  "lightburn_out_port": 19840,        // Port to send commands (default)
  "lightburn_in_port": 19841,         // Port to receive responses (default)
  "lightburn_timeout": 2.0,           // Response timeout in seconds
  "lightburn_poll_interval": 0.5,     // How often to check status (seconds)
  "lightburn_max_wait": 300,          // Max wait time for job completion (5 minutes)
  "use_lightburn_status": true        // Use status monitoring vs pause timer
}
```

### Important Settings

- **use_lightburn_status**: Set to `true` to use real-time status monitoring. Set to `false` to fall back to the old pause timer.
- **lightburn_max_wait**: Maximum time to wait for a job to complete (300 seconds = 5 minutes default)
- **pause_seconds**: Fallback timer if LightBurn status monitoring is disabled or fails

## How It Works During Cycle

When processing each key, the system now:

1. **Detects key** with inductive sensor
2. **Triggers Pico** keyboard emulator (sends Enter key)
3. **Starts LightBurn job** via UDP (START command)
4. **Polls LightBurn status** every 0.5 seconds
5. **Waits for "IDLE"** status (job complete)
6. **Continues to next key** once LightBurn reports completion

### Comparison: Old vs New Behavior

**Old Behavior (Pause Timer):**
```
Detect Key → Trigger Pico → Wait Fixed Time (e.g., 10s) → Next Key
```
Problem: If job takes 8 seconds, you wait extra 2 seconds. If job takes 12 seconds, it gets interrupted.

**New Behavior (Status Monitoring):**
```
Detect Key → Trigger Pico → Start Job → Poll Status → Wait for Complete → Next Key
```
Advantage: System automatically waits exactly as long as needed, no more, no less.

## Troubleshooting

### "LightBurn not responding" Error

**Possible causes:**
1. LightBurn not running on Mac
2. UDP automation not enabled in LightBurn
3. Wrong IP address configured
4. Firewall blocking UDP ports
5. Mac and Pi on different networks

**Solutions:**
- Verify LightBurn is running and a file is loaded
- Check Device Settings → Enable UDP
- Verify Mac IP address matches config
- Temporarily disable Mac firewall to test
- Ensure both devices are on same WiFi network

### Status Check Shows "Failed to get status"

**Possible causes:**
1. LightBurn UDP automation disabled
2. LightBurn busy and not responding
3. Network timeout

**Solutions:**
- Restart LightBurn
- Enable UDP automation in settings
- Increase `lightburn_timeout` in config

### Jobs Don't Start Automatically

**Check:**
1. `lightburn_enabled` is `true` in config
2. `use_lightburn_status` is `true` in config
3. Test connection works on config page
4. Check Raspberry Pi console logs for error messages

## Fallback Mode

If LightBurn status monitoring fails for any reason, the system automatically falls back to using the `pause_seconds` timer. This ensures your process continues even if LightBurn communication is lost.

To **force fallback mode**, set `use_lightburn_status` to `false` in the config.

## API Endpoints

For advanced users and debugging:

- `POST /api/lightburn/ping` - Test connection
- `GET /api/lightburn/status` - Get current status
- `POST /api/lightburn/start` - Start job manually

## Network Ports Reference

| Port  | Direction | Purpose                          |
|-------|-----------|----------------------------------|
| 5005  | Pi → Mac  | Legacy UDP trigger (backward compatible) |
| 19840 | Pi → Mac  | LightBurn command port (outgoing) |
| 19841 | Mac → Pi  | LightBurn response port (incoming) |

## References

- LightBurn Automation: https://github.com/bunkford/lightburn_automation
- LightBurn Documentation: https://docs.lightburnsoftware.com/

## Support

If you encounter issues:
1. Check Mac firewall settings
2. Verify network connectivity (ping Mac from Pi)
3. Test with manual "Start Job" button on config page
4. Check console logs on Raspberry Pi for detailed error messages
5. Try fallback mode (disable `use_lightburn_status`) as temporary workaround

