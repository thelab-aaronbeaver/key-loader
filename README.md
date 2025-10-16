# Key Loader - Rotary Table Control System

A Raspberry Pi-based automated key processing system that uses a rotary table with proximity detection and slider actuation for key loading operations.

## Overview

This system automates the process of detecting keys on a rotating table and triggering a slider mechanism to process them. The system consists of:

- **Rotary Motor**: [OMC NEMA 23 Closed Loop Stepper Kit](https://www.omc-stepperonline.com/ts-series-1-axis-3-0nm-424-83oz-in-nema-23-closed-loop-stepper-kit-w-power-supply-1-clts30a-v41) - 3.0Nm (424.83 oz-in) with integrated driver and power supply
- **Slider Motor**: Moves in/out to process detected keys
- **Hall Sensor**: Detects home position (magnet-based)
- **Inductive Proximity Sensor**: Detects brass/metal keys
- **Limit Switches**: Safety stops for slider movement
- **Raspberry Pico Integration**: External timer/control system

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
| Rotary Alarm | 16 | Motor stall detection (ALM+) |
| Hall Sensor | 26 | Home position detection |
| Inductive Sensor | 19 | Key detection |
| Slider Step | 23 | Slider motor step signal |
| Slider Dir | 24 | Slider motor direction |
| Slider IN | 13 | Slider inward limit switch |
| Slider OUT | 12 | Slider outward limit switch |
| Home Switch | 5 | Legacy home switch (optional) |
| End Switch | 6 | Legacy end switch (optional) |

**Note**: The OMC closed-loop stepper uses differential signals (PUL+/PUL-, DIR+/DIR-, ALM+/ALM-). Connect PUL+, DIR+, ALM+ to Raspberry Pi GPIO pins, and PUL-, DIR-, ALM- to Pi ground.

### Software Components

- **Flask Web Server**: Main application server
- **Hardware Controller**: GPIO interface and motor control
- **Configuration System**: JSON-based settings persistence
- **Web Interface**: Control and configuration pages

## Application Logic

### 1. Initialization
- Load configuration from `config.json`
- Initialize GPIO pins and motor controllers
- Set up web server routes

### 2. Homing Sequence
- Rotate rotary motor until hall sensor detects magnet
- Set current position as 0° reference
- Mark system as "homed" and ready for operation

### 3. Cycle Operation
The main processing cycle follows this sequence:

```
For each cycle step:
1. Move rotary motor by configured step degrees
2. Verify position with hall sensor
3. Check inductive sensor for key presence
4. If key detected:
   a. Send trigger command to Raspberry Pico
   b. Move slider to IN limit switch
   c. Move slider to OUT limit switch
   d. Wait for configured pause time
   e. Continue to next position
5. If no key: Continue to next position
6. Repeat for configured number of cycles
```

### 4. Key Detection Process
When a key is detected:
1. **Trigger Pico**: Send command to external Raspberry Pico
2. **Slider IN**: Move slider to inward limit switch
3. **Slider OUT**: Move slider to outward limit switch
4. **Pause**: Wait for poles timer (configurable duration)
5. **Continue**: Proceed to next rotary position

## Configuration

Settings are stored in `config.json` and can be modified via the web interface:

```json
{
  "step_degrees": 36.0,        // Rotary movement per step
  "pause_seconds": 1.0,        // Pause time after key processing
  "slider_in_speed": 50,       // Slider IN speed (0-100)
  "slider_out_speed": 50,      // Slider OUT speed (0-100)
  "cycles": 10                 // Default number of cycles
}
```

### Speed Scale
- **0**: Stopped (very slow)
- **50**: Medium speed (default)
- **100**: Fastest speed

## Web Interface

### Main Control Page (`/`)
- **Status Display**: Current angle, homing status, sensor states
- **Control Buttons**: Home machine, start cycle
- **Cycle Input**: Number of cycles to run
- **Real-time Updates**: Live sensor status and system messages

### Configuration Page (`/config`)
- **Rotary Controls**: Home, set zero, manual movement
- **Process Settings**: Step degrees, pause time, slider speeds
- **Sensor Verification**: Live status of all sensors
- **Save Configuration**: Persist settings to JSON file

## API Endpoints

### Control Endpoints
- `POST /api/home` - Home the rotary motor
- `POST /api/start` - Start processing cycle
- `GET /api/status` - Get current system status

### Configuration Endpoints
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/rotary/home` - Home rotary motor (config page)
- `POST /api/rotary/move` - Move rotary motor by degrees
- `POST /api/rotary/set_zero` - Set current position as zero

## Installation & Setup

### Prerequisites
- Raspberry Pi with GPIO access
- Python 3.7+
- Flask web framework
- RPi.GPIO library

### Installation
```bash
# Clone repository
git clone <repository-url>
cd key-loader

# Install dependencies
pip install flask RPi.GPIO

# Run application
python app.py
```

### Hardware Setup

#### Rotary Motor (OMC NEMA 23 Closed Loop)
1. **Power Connection**: Connect included 24V/5A power supply to motor driver
2. **Signal Wiring**: 
   - PUL+ → GPIO 20 (Raspberry Pi)
   - PUL- → Ground (Raspberry Pi)
   - DIR+ → GPIO 21 (Raspberry Pi)
   - DIR- → Ground (Raspberry Pi)
   - ALM+ → GPIO 16 (Raspberry Pi)
   - ALM- → Ground (Raspberry Pi)
3. **Motor Configuration**: Set microstepping via DIP switches (recommend 16x for smooth operation)
4. **Closed-Loop Setup**: Configure encoder and tuning via OMC software if needed

#### General Setup
1. Connect slider motor to specified GPIO pins
2. Wire sensors and limit switches with pull-up resistors
3. Ensure proper power supply for all motors
4. Connect Raspberry Pico for external control
5. Test all connections before powering on

### Configuration
1. Access web interface at `http://<pi-ip>:5000`
2. Navigate to Configuration page
3. Adjust settings as needed
4. Save configuration
5. Test homing and manual movements

## Safety Features

- **Motor Stall Detection**: Stops operation if motor stalls
- **Limit Switch Protection**: Prevents over-travel
- **Position Verification**: Confirms movements with hall sensor
- **Error Handling**: Graceful failure with clear error messages
- **Emergency Stop**: Can be implemented via web interface

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
   - Ensure differential signal wiring (PUL+/PUL-, DIR+/DIR-)
   - Check microstepping DIP switch settings
   - Verify closed-loop controller is properly configured
   - Test with OMC configuration software

### Debug Information
- Check console output for GPIO and motor status
- Use configuration page to verify sensor states
- Monitor system messages in web interface

## Development

### File Structure
```
key-loader/
├── app.py                 # Main Flask application
├── hardware_controller.py # GPIO and motor control
├── config.json           # Configuration settings
├── templates/
│   ├── index.html        # Main control page
│   └── config.html       # Configuration page
├── static/
│   ├── style.css         # Shared styles
│   ├── script.js         # Main page JavaScript
│   └── config.js         # Config page JavaScript
└── README.md             # This file
```

### Adding Features
- **Pico Communication**: Implement actual serial/USB communication in `send_pico_command()`
- **Background Processing**: Move long operations to background threads
- **Logging**: Add file-based logging for operation history
- **Advanced Safety**: Add emergency stop and soft limits

## License

This project is designed for specific hardware configurations. Modify as needed for your setup.

## Support

For issues or questions, check the troubleshooting section or review the code comments for implementation details.
