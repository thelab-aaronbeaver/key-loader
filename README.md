# Key Loader - Rotary Table Control System

A Raspberry Pi-based automated key processing system that uses a rotary table with proximity detection, slider actuation, and LightBurn laser integration for automated key engraving operations.

## Overview

This system automates the process of detecting keys on a rotating table, triggering LightBurn laser jobs, and processing them with synchronized mechanical movements. The system consists of:

- **Rotary Motor**: [OMC NEMA 23 Closed Loop Stepper Kit](https://www.omc-stepperonline.com/ts-series-1-axis-3-0nm-424-83oz-in-nema-23-closed-loop-stepper-kit-w-power-supply-1-clts30a-v41) - 3.0Nm (424.83 oz-in) with integrated driver and power supply
- **Slider Motor**: Moves in/out to process detected keys
- **Hall Sensor**: Detects home position (magnet-based)
- **Inductive Proximity Sensor**: Detects brass/metal keys
- **Limit Switches**: Safety stops for slider movement
- **LightBurn Integration**: Automated laser engraving with real-time status monitoring via UDP

## System Architecture

### Hardware Components

#### Rotary Motor Specifications
- **Model**: OMC NEMA 23 Closed Loop Stepper Kit (CLTS30A-V4.1)
- **Torque**: 3.0Nm (424.83 oz-in)
- **Step Angle**: 1.8° (200 steps/revolution)
- **Microstepping**: Configurable (typically 16x = 3200 steps/revolution)
- **Driver**: Integrated closed-loop controller
- **Power Supply**: Included 24V/5A supply

#### GPIO Pin Configuration

| Component | GPIO Pin | Function |
|-----------|----------|----------|
| Rotary Step | 20 | Stepper motor step signal (PUL+) |
| Rotary Dir | 21 | Stepper motor direction (DIR+) |
| Rotary Enable | 19 | Motor enable/disable control (EN+) |
| Rotary Alarm | 16 | Motor stall detection (ALM+) |
| Hall Sensor | 26 | Home position detection |
| Inductive Sensor | 22 | Key detection |
| Slider Step | 23 | Slider motor step signal |
| Slider Dir | 24 | Slider motor direction |
| Slider Enable | 25 | Slider motor enable/disable control |
| Slider Alarm | 18 | Slider motor stall detection |
| Slider MIN | 27 | Slider inward limit switch |
| Slider MAX | 17 | Slider outward limit switch |
| Home Switch | 5 | Legacy home switch (optional) |
| End Switch | 6 | Legacy end switch (optional) |

**Note**: The OMC closed-loop stepper uses differential signals (PUL+/PUL-, DIR+/DIR-, EN+/EN-, ALM+/ALM-). Connect PUL+, DIR+, EN+, ALM+ to Raspberry Pi GPIO pins, and PUL-, DIR-, EN-, ALM- to Pi ground.

### Software Components

- **Flask Web Server**: Main application server with WebSocket support
- **Hardware Controller**: GPIO interface and motor control
- **LightBurn Controller**: UDP communication for laser automation
- **Configuration System**: JSON-based settings persistence
- **Web Interface**: Control and configuration pages with real-time updates
- **Performance Monitoring**: Comprehensive timing and statistics tracking

## Application Logic

### 1. Initialization
- Load configuration from `config.json`
- Initialize GPIO pins and motor controllers
- Set up web server routes

### 2. Homing Sequence
- Rotate rotary motor until hall sensor detects magnet
- Set current position as 0° reference
- Mark system as "homed" and ready for operation

### 3. Key-Driven Cycle Operation
The system operates as a continuous key detection and processing machine with integrated laser engraving:

```
Start State:
0. Check hall sensor at 0° position
1. Position slider to OUT (MAX) limit switch

Key-Driven Cycle Loop:
For each position until target keys are processed:
1. Check inductive sensor for key presence
2. If KEY DETECTED:
   a. Start LightBurn job via UDP
   b. Poll LightBurn status every 100ms
   c. Wait for job completion (status: IDLE)
   d. Move rotary motor to next position
   e. Move slider MAX → MIN → MAX
   f. Count as processed key
3. If NO KEY DETECTED:
   a. Move rotary motor by step degrees
   b. Move slider MAX → MIN → MAX (search pattern)
   c. Hold at MAX until next cycle
4. Continue until target number of keys processed
```

### 4. Key Processing Sequence (with LightBurn Integration)
When a key is detected:
1. **Start LightBurn Job**: Send UDP START command to LightBurn
2. **Monitor Job Status**: Poll LightBurn every 100ms checking for completion
3. **Wait for Completion**: Continue polling until status returns "OK" (idle)
4. **Log Performance**: Record LightBurn job duration and total processing time
5. **Mechanical Processing**: Move rotary to next position, move slider MAX → MIN → MAX
6. **Progress Update**: Count as processed key and continue search

**Status Monitoring:**
- Job Running: LightBurn returns `"!"` status
- Job Complete: LightBurn returns `"OK"` status
- Fallback: If status monitoring fails, uses pause timer

### 5. Continuous Search Pattern
When no key is detected:
1. **Rotary Movement**: Move to next position by step degrees
2. **Search Pattern**: Move slider MAX → MIN → MAX
3. **Hold Position**: Stay at MAX limit switch until next cycle
4. **Repeat**: Continue searching until key is found

## Configuration

Settings are stored in `config.json` and can be modified via the web interface:

```json
{
  "step_degrees": 36.0,              // Rotary movement per step (degrees)
  "pause_seconds": 1.0,              // Fallback pause time (used if LightBurn status monitoring disabled)
  "slider_in_speed": 90,             // Slider IN speed (0-100)
  "slider_out_speed": 90,            // Slider OUT speed (0-100)
  "slider_accel_steps": 20,          // Slider acceleration ramp steps
  "slider_decel_steps": 20,          // Slider deceleration ramp steps
  "rotary_speed": 100,               // Rotary motor speed (0-100)
  "rotary_accel_steps": 50,          // Rotary acceleration ramp steps
  "rotary_decel_steps": 50,          // Rotary deceleration ramp steps
  "cycles": 10,                      // Default number of keys to process
  "home_offset": 0.0,                // Fine-tune home position offset (degrees)
  
  // LightBurn Integration Settings
  "lightburn_enabled": true,         // Enable/disable LightBurn integration
  "lightburn_ip": "192.168.1.170",   // IP address of Mac/PC running LightBurn
  "lightburn_out_port": 19840,       // LightBurn UDP command port
  "lightburn_in_port": 19841,        // LightBurn UDP response port
  "lightburn_timeout": 2.0,          // Response timeout (seconds)
  "lightburn_poll_interval": 0.1,    // Status check interval (0.1s = 100ms)
  "lightburn_max_wait": 300,         // Maximum wait for job completion (5 minutes)
  "use_lightburn_status": true,      // Use status monitoring vs pause timer
  
  // Legacy UDP Trigger (backward compatibility)
  "udp_enabled": true,               // Enable legacy UDP trigger
  "udp_ip": "192.168.1.170",         // Legacy UDP target IP
  "udp_port": 5005,                  // Legacy UDP port
  "udp_message": "START"             // Legacy UDP message
}
```

### Speed Scale
- **0**: Stopped (very slow)
- **50**: Medium speed
- **75+**: Fast speed (enables ultra-fast mode for slider)
- **100**: Maximum speed

### LightBurn Integration
The system uses UDP automation to communicate with LightBurn:
- **Port 19840**: Sends commands (START, STATUS, PING)
- **Port 19841**: Receives responses from LightBurn
- **Status Polling**: Checks job status every 100ms
- **Dynamic Timing**: Waits exactly as long as job takes (no fixed delays)

## Web Interface

### Main Control Page (`/`)
- **Status Display**: Current angle, homing status, sensor states
- **Control Buttons**: Home machine, start cycle
- **Cycle Input**: Number of cycles to run
- **Real-time Updates**: Live sensor status and system messages

### Configuration Page (`/config`)
- **LightBurn Integration**: Test connection, check status, manual job start
- **Rotary Controls**: Home, set zero, manual movement
- **Slider Motor Test**: Test slider cycle (MIN→MAX)
- **Process Settings**: Step degrees, speeds, acceleration, LightBurn settings
- **Sensor Verification**: Live status of all sensors and limit switches
- **Save Configuration**: Persist settings to JSON file

## API Endpoints

### Control Endpoints
- `POST /api/home` - Home the rotary motor
- `POST /api/start` - Start processing cycle
- `POST /api/stop` - Stop current cycle at next safe point
- `POST /api/emergency_stop` - Immediately halt all motion
- `POST /api/emergency_stop_reset` - Reset emergency stop state
- `GET /api/status` - Get current system status

### Configuration Endpoints
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/rotary/home` - Home rotary motor (config page)
- `POST /api/rotary/move` - Move rotary motor by degrees
- `POST /api/rotary/set_zero` - Set current position as zero
- `POST /api/slider/test_cycle` - Test slider motor cycle (MIN→MAX)

### LightBurn Integration Endpoints
- `POST /api/lightburn/ping` - Test LightBurn connection
- `GET /api/lightburn/status` - Get LightBurn job status
- `POST /api/lightburn/start` - Manually start LightBurn job
- `POST /api/udp/test` - Test legacy UDP trigger

## Installation & Setup

### Prerequisites
- Raspberry Pi with GPIO access
- Python 3.7+
- Flask web framework and Flask-SocketIO
- RPi.GPIO library
- LightBurn software on Mac/PC (for laser engraving)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd key-loader

# Install dependencies
pip install -r requirements.txt
# or manually:
pip install flask flask-socketio RPi.GPIO

# Run application
python app.py
```

### LightBurn Setup (Mac/PC)
1. **Enable UDP Automation in LightBurn:**
   - Open LightBurn
   - Go to Edit → Device Settings
   - Enable UDP Listening
   - Set ports: 19840 (incoming), 19841 (outgoing)

2. **Configure Network:**
   - Ensure Mac/PC and Raspberry Pi are on same network
   - Note Mac/PC IP address (e.g., 192.168.1.170)
   - Configure firewall to allow UDP ports 19840/19841

3. **Test Connection:**
   - Access web interface configuration page
   - Click "Test Connection" in LightBurn Integration section
   - Should show "Connected" if properly configured

See `LIGHTBURN_SETUP.md` for detailed instructions.

### Hardware Setup

#### Rotary Motor (OMC NEMA 23 Closed Loop)
1. **Power Connection**: Connect included 24V/5A power supply to motor driver
2. **Signal Wiring**: 
   - PUL+ → GPIO 20 (Raspberry Pi)
   - PUL- → Ground (Raspberry Pi)
   - DIR+ → GPIO 21 (Raspberry Pi)
   - DIR- → Ground (Raspberry Pi)
   - EN+ → GPIO 19 (Raspberry Pi)
   - EN- → Ground (Raspberry Pi)
   - ALM+ → GPIO 16 (Raspberry Pi)
   - ALM- → Ground (Raspberry Pi)
3. **Motor Configuration**: Set microstepping via DIP switches (recommend 16x for smooth operation)
4. **Closed-Loop Setup**: Configure encoder and tuning via OMC software if needed

#### General Setup
1. Connect slider motor to specified GPIO pins
2. Wire sensors and limit switches with pull-up resistors
3. Ensure proper power supply for all motors
4. Set up LightBurn on Mac/PC with UDP automation enabled
5. Test all connections before powering on

### Configuration
1. Access web interface at `http://<pi-ip>:5000`
2. Navigate to Configuration page
3. Adjust settings as needed
4. Save configuration
5. Test homing and manual movements

## Safety Features

- **Motor Stall Detection**: Stops operation if rotary or slider motor stalls
- **Limit Switch Protection**: Prevents slider over-travel with MIN/MAX switches
- **Position Verification**: Confirms movements with hall sensor
- **Error Handling**: Graceful failure with clear error messages and logging
- **Emergency Stop**: Immediate halt of all motion via web interface
- **Timeout Protection**: Maximum wait time for LightBurn jobs (5 minutes default)
- **Status Monitoring**: Real-time tracking of all sensors and motor states

## Troubleshooting

### Common Issues
1. **Homing Fails**: Check hall sensor wiring and magnet placement
2. **Motor Stalls**: 
   - Verify 24V power supply is connected and adequate
   - Check for mechanical binding or overload
   - Verify closed-loop tuning and encoder connection
   - Check ALM signal wiring (should be HIGH when motor is OK)
3. **Sensors Not Working**: Check wiring and pull-up resistors
4. **Web Interface Unavailable**: Verify Flask server is running
5. **Rotary Motor Issues**:
   - Ensure differential signal wiring (PUL+/PUL-, DIR+/DIR-, EN+/EN-)
   - Check enable pin wiring (EN+ to GPIO 19, EN- to ground)
   - Verify motor is enabled before movement
   - Check microstepping DIP switch settings
   - Verify closed-loop controller is properly configured
   - Test with OMC configuration software

### Debug Information
- Check console output for GPIO and motor status
- Use configuration page to verify sensor states
- Monitor system messages in web interface

## Performance Monitoring

The system tracks comprehensive timing statistics:

### Cycle Statistics
- **Total Cycle Time**: Complete cycle duration from start to finish
- **Keys Processed**: Number of keys successfully engraved
- **Average Time per Key**: Mean processing time including mechanical movements

### Individual Key Timing
- **LightBurn Job Duration**: Actual laser engraving time
- **Total Key Time**: Complete processing time (LightBurn + mechanical)
- **Mechanical Overhead**: Time spent on movements vs laser work

### Example Console Output
```
================================================================================
🚀 CYCLE STARTED - Processing 10 keys
================================================================================

────────────────────────────────────────────────────────────────────────────────
🔑 KEY 5/10 - Position 5 (180°)
────────────────────────────────────────────────────────────────────────────────
⏱️  LightBurn job duration: 6.35s
✅ Key 5 complete - Total time: 11.82s (LightBurn: 6.35s)
────────────────────────────────────────────────────────────────────────────────

================================================================================
📊 CYCLE STATISTICS
================================================================================
Keys Processed: 10/10
Total Cycle Time: 145.67s (2.4 minutes)
Average Time per Key: 14.57s
================================================================================
```

## Development

### File Structure
```
key-loader/
├── app.py                    # Main Flask application with WebSocket
├── hardware_controller.py    # GPIO and motor control
├── lightburn_controller.py   # LightBurn UDP communication
├── config.json               # Configuration settings
├── requirements.txt          # Python dependencies
├── templates/
│   ├── index.html           # Main control page
│   └── config.html          # Configuration page
├── static/
│   ├── style.css            # Shared styles
│   ├── script.js            # Main page JavaScript
│   └── config.js            # Config page JavaScript
├── README.md                # This file
├── LIGHTBURN_SETUP.md       # LightBurn integration guide
├── INTEGRATION_SUMMARY.md   # Technical implementation details
└── CHANGELOG.md             # Version history and changes
```

### Key Features
- **Real-time WebSocket Updates**: Live sensor and status monitoring
- **Background Threading**: Non-blocking cycle execution
- **Comprehensive Logging**: Detailed timing and performance metrics
- **Fallback Mechanisms**: Automatic graceful degradation if LightBurn offline
- **Thread-Safe State Management**: Prevents race conditions in multi-threaded environment

### Adding Features
- **Extended Monitoring**: Add database logging for historical analysis
- **Advanced Analytics**: Generate performance graphs and trends
- **Remote Control**: Add API authentication for remote access
- **Multi-Machine Support**: Control multiple LightBurn instances

## Technical Documentation

- **LIGHTBURN_SETUP.md** - Detailed LightBurn configuration guide for Mac/PC
- **INTEGRATION_SUMMARY.md** - Technical details of LightBurn integration
- **CHANGELOG.md** - Version history and recent changes
- **TROUBLESHOOTING.md** - Common issues and solutions
- **UDP_INTEGRATION_GUIDE.md** - UDP communication protocol details
- **WIRING_DIAGRAM.md** - Complete hardware wiring guide

## Version History

**v2.0** (Current)
- ✅ LightBurn UDP automation integration
- ✅ Real-time job status monitoring
- ✅ Comprehensive timing and statistics
- ✅ Removed Raspberry Pico dependency
- ✅ Dynamic job completion detection
- ✅ WebSocket real-time updates
- ✅ Emergency stop functionality

**v1.0**
- Initial release with basic motor control
- Hall sensor homing
- Manual Pico keyboard emulation
- Fixed pause timers

## Credits

- LightBurn UDP Integration based on: https://github.com/bunkford/lightburn_automation
- Rotary motor: OMC NEMA 23 Closed Loop Stepper Kit

## License

This project is designed for specific hardware configurations. Modify as needed for your setup.

## Support

For issues or questions:
1. Check console logs for detailed timing and error information
2. Review **TROUBLESHOOTING.md** for common issues
3. Test LightBurn connection using web interface
4. Verify all sensor states on configuration page
5. Check **LIGHTBURN_SETUP.md** for Mac/PC configuration

## Quick Start

1. **Hardware Setup**: Wire all components according to GPIO pin configuration
2. **Software Install**: `pip install -r requirements.txt`
3. **LightBurn Config**: Enable UDP automation on Mac/PC (ports 19840/19841)
4. **Network Setup**: Ensure Pi and Mac/PC on same network
5. **Test Connection**: Access web interface, test LightBurn connection
6. **Home Machine**: Click "Home Machine" on main page
7. **Start Cycle**: Enter number of keys and click "Start Cycle"
8. **Monitor Progress**: Watch real-time updates and timing statistics

For detailed setup instructions, see **LIGHTBURN_SETUP.md**.
