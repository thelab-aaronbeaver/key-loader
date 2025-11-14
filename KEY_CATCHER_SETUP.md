# Key Catcher Motor Integration Guide

## Overview

A new MKS SERVO42C NEMA17 Closed Loop Stepper Motor Driver has been added to control a key catching device. This motor automatically rotates to collect keys as they are processed, with automatic pausing for key removal after a configurable number of keys.

---

## Hardware Setup

### GPIO Pin Assignments

The key catcher motor uses the following GPIO pins (BCM numbering):

| Pin Function | GPIO Pin | Description |
|--------------|----------|-------------|
| STEP | GPIO 12 | Step signal (PUL+) |
| DIR | GPIO 13 | Direction signal (DIR+) |
| ENABLE | GPIO 14 | Enable/Disable (ENA) |

### Power Requirements

- **Power Supply**: External 12V power supply (dedicated)
- **Current**: Set motor driver for your motor rating (typically 1-2A)
- **Ground**: Connect to common ground with main system

### DIP Switch Settings

Configure the MKS SERVO42C driver for 4x microstepping:
- **MS1**: OFF
- **MS2**: ON  
- **MS3**: OFF

This gives 800 steps per revolution (optimized for 12V operation).

---

## Wiring Diagram

```
External 12V Supply          MKS SERVO42C Driver          Key Catcher Motor
┌─────────────┐             ┌──────────────────┐         ┌──────────────┐
│ 12V+ ───────┼─────────────┤ VCC              │         │ A+           │
│ GND ────────┼─────────────┤ GND              │         │ A-           │
└─────────────┘             │                  ├─────────┤ B+           │
                            │                  │         │ B-           │
Raspberry Pi 4              │                  │         └──────────────┘
┌─────────────┐             │                  │
│ GPIO 12 ────┼─────────────┤ PUL+             │
│ GPIO 13 ────┼─────────────┤ DIR+             │
│ GPIO 14 ────┼─────────────┤ ENA              │
│ GND ────────┼─────────────┤ GND              │
└─────────────┘             └──────────────────┘

⚠️  IMPORTANT: Connect external 12V supply ground to Raspberry Pi ground
```

---

## Software Features

### Configuration Settings

All settings can be adjusted in the configuration page (`/config`):

| Setting | Default | Description |
|---------|---------|-------------|
| Enable Key Catcher | Enabled | Turn on/off automatic key catcher movement |
| Steps Per Key | 80 | Number of steps to move per key processed |
| Speed | 80 | Motor speed (0-100, where 100 = 750 RPM max) |
| Start Position | 0 | Home position in steps |
| Pause Position | 4000 | Position after N keys (calculated: 50 keys × 80 steps) |
| Keys Before Pause | 50 | Number of keys to process before pausing for removal |

### Operation Flow

1. **Start Position**: Motor begins at configured start position (default: 0 steps)
2. **Key Processing**: 
   - Each time a key is detected and processed, motor moves forward by "Steps Per Key"
   - Position is tracked automatically
3. **Pause for Removal**:
   - After processing the configured number of keys (default: 50), cycle pauses
   - System displays: "⏸️ PAUSED: Remove keys and click RESUME"
   - Resume button appears on main control page
4. **Resume**:
   - Click "Resume Cycle" button
   - Motor automatically returns to start position
   - Key counter resets to 0
   - Cycle continues

---

## Testing & Calibration

### Position Testing (Configuration Page)

1. Navigate to `/config` → **Key Catcher Motor** section
2. Use these controls to test and calibrate:

**Test Movement:**
- **Steps to Move**: Enter step count (positive/negative)
- **Move Steps**: Execute the movement
- **Current Position**: Displays current position in steps

**Absolute Positioning:**
- **Target Position**: Enter desired position
- **Go To Position**: Move to exact position

**Reset:**
- **Reset to Home**: Return to position 0

### Setting Start and Pause Positions

1. **Set Start Position**:
   - Use position controls to move to desired start location
   - Click **"Set as Start Position"**
   - Click **"Save"** to persist

2. **Set Pause Position**:
   - Move to desired position after N keys
   - Click **"Set as Pause Position"**
   - Click **"Save"** to persist

---

## API Endpoints

The following API endpoints are available for integration:

### Testing Endpoints

```bash
# Move specific number of steps
POST /api/key_catcher/move_steps
Body: {"steps": 80, "speed": 80}

# Move to absolute position
POST /api/key_catcher/move_to_position
Body: {"position": 1000, "speed": 80}

# Reset to home position (0)
POST /api/key_catcher/reset

# Set current position as specific value (calibration)
POST /api/key_catcher/set_position
Body: {"position": 0}

# Get current position and key count
GET /api/key_catcher/get_position
Response: {"success": true, "position": 1600, "keys_processed": 20}
```

### Cycle Control

```bash
# Resume after pause (resets to start position)
POST /api/key_catcher/resume
```

---

## Troubleshooting

### Motor Not Moving

1. **Check Power Supply**: Verify 12V external supply is connected and powered
2. **Check Enable Pin**: Motor driver should show enabled (LED indicator)
3. **Check Wiring**: Verify GPIO 12, 13, 14 connections
4. **Check DIP Switches**: Ensure 4x microstepping (MS1=OFF, MS2=ON, MS3=OFF)

### Position Tracking Issues

1. **Lost Position**: If motor stalls or loses position:
   - Stop cycle
   - Use "Reset to Home" in testing section
   - Manually verify physical position
   - Use "Set Position" to recalibrate if needed

2. **Incorrect Movement**: If motor moves wrong distance:
   - Verify "Steps Per Key" setting
   - Check motor driver microstepping configuration
   - Test with known step count using "Move Steps"

### Pause Not Working

1. **Check Configuration**: Verify "Keys Before Pause" is set correctly
2. **Check Enable**: Ensure "Enable Key Catcher" is checked
3. **Console Logs**: Check terminal output for pause messages

---

## Advanced Configuration

### Calculating Pause Position

Pause position should equal:
```
Pause Position = Keys Before Pause × Steps Per Key
```

Example:
- Keys Before Pause: 50
- Steps Per Key: 80
- Pause Position: 50 × 80 = 4000 steps

### Speed Optimization

The key catcher motor uses the same speed calculation as the slider motor:
- **Speed 100**: 750 RPM maximum (12V supply)
- **Speed 50**: 375 RPM
- **Speed 80**: 600 RPM (recommended)

Higher speeds may require:
- Higher supply voltage (24V recommended for maximum speed)
- Adjusted microstepping (2x instead of 4x)
- Increased current limit on driver

---

## Safety Notes

⚠️ **Important Safety Information**:

1. **Emergency Stop**: E-Stop button halts ALL motors including key catcher
2. **Power Isolation**: Use dedicated 12V supply to prevent ground loops
3. **Manual Intervention**: Motor will pause and wait for user input - safe for key removal
4. **Position Tracking**: System tracks position in software - homing not currently implemented
5. **Mechanical Limits**: No limit switches - ensure mechanical design prevents over-travel

---

## Integration with Main Cycle

The key catcher motor is fully integrated into the main cycle:

```
Main Cycle Flow:
1. Home machine
2. Start cycle
3. For each key:
   a. Detect key
   b. Process key (LightBurn + Slider movements)
   c. Move rotary to next position
   d. → Move key catcher motor ← (NEW)
   e. Check if pause needed
4. If pause:
   a. Display pause message
   b. Wait for user to click Resume
   c. Reset key catcher to start position
   d. Continue cycle
```

---

## Configuration File Structure

The key catcher settings are stored in `config.json`:

```json
{
  "key_catcher_enabled": true,
  "key_catcher_steps_per_key": 80,
  "key_catcher_speed": 80,
  "key_catcher_start_position": 0,
  "key_catcher_pause_position": 4000,
  "key_catcher_keys_before_pause": 50
}
```

---

## Next Steps

1. **Wire the motor** according to the wiring diagram above
2. **Power on** the external 12V supply
3. **Test movement** using the configuration page controls
4. **Calibrate positions** by setting start and pause positions
5. **Test full cycle** with a small number of keys (e.g., 5-10)
6. **Adjust settings** as needed for your mechanical setup

---

## Support & Modifications

All code changes are complete and integrated. Key files modified:

- `hardware_controller.py` - Motor control methods
- `app.py` - API endpoints and cycle integration
- `config.json` - Default settings
- `templates/config.html` - Testing UI
- `templates/index.html` - Resume button
- `static/config.js` - Configuration page JavaScript
- `static/script.js` - Main page JavaScript
- `WIRING_DIAGRAM.md` - Updated with key catcher pins

For further customization, adjust settings in the configuration page or edit `config.json` directly.

