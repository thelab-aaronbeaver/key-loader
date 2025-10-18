# Key Loader Troubleshooting Guide

## Issue: No Response from Motors or Limit Switches

### Quick Diagnosis Steps

1. **Check if you're running on Raspberry Pi**
   - This code only works on Raspberry Pi hardware
   - Windows/Mac cannot access GPIO pins

2. **Verify Hardware Power**
   - Raspberry Pi is powered on and accessible
   - 24V power supply is connected to OMC stepper driver
   - Motor driver power LED is illuminated
   - All connections are secure

### Detailed Troubleshooting

#### 1. Software Setup Issues

**Problem**: RPi.GPIO library not installed
```bash
# On Raspberry Pi, install the library:
pip install RPi.GPIO
# or
sudo apt-get install python3-rpi.gpio
```

**Problem**: Permission denied for GPIO access
```bash
# Add user to gpio group:
sudo usermod -a -G gpio $USER
# Then logout and login again
```

**Problem**: Another process using GPIO
```bash
# Check for running processes:
ps aux | grep python
# Kill any conflicting processes
```

#### 2. Motor Wiring Issues (OMC Closed-Loop Stepper)

**Critical**: OMC steppers use differential signals. You MUST connect both + and - signals:

```
Raspberry Pi GPIO 20 (PUL+)  ->  OMC Driver PUL+
Raspberry Pi Ground          ->  OMC Driver PUL-
Raspberry Pi GPIO 21 (DIR+)  ->  OMC Driver DIR+
Raspberry Pi Ground          ->  OMC Driver DIR-
Raspberry Pi GPIO 22 (EN+)   ->  OMC Driver EN+
Raspberry Pi Ground          ->  OMC Driver EN-
Raspberry Pi GPIO 16 (ALM+)  ->  OMC Driver ALM+
Raspberry Pi Ground          ->  OMC Driver ALM-
```

**Common Mistakes**:
- Only connecting + signals (missing - connections to ground)
- Reversing + and - connections
- Using wrong GPIO pins
- **Missing enable pin connections** (EN+/EN-)
- Not enabling motor before movement

#### 3. Enable Pin Functionality

**Enable Pin Behavior**:
- **LOW (0V)**: Motor enabled, can move and hold position
- **HIGH (3.3V)**: Motor disabled, freewheels (no holding torque)
- **Default State**: Motors start disabled for safety

**Why Enable Pins Matter**:
- **Power Management**: Reduces heat and power consumption when idle
- **Safety**: Prevents unwanted movement during setup
- **Position Holding**: Enabled motors hold position, disabled motors freewheel
- **Control**: Allows software to enable/disable motors as needed

#### 4. Motor Driver Configuration

**DIP Switch Settings** (check your OMC driver):
- Microstepping: Set to 16x (3200 steps/revolution)
- Current: Set appropriate for your motor
- Mode: Closed-loop enabled

**Power Supply**:
- Must be 24V DC, minimum 5A
- Check voltage with multimeter
- Ensure adequate current capacity

#### 5. Sensor Wiring Issues

**Hall Sensor (Home Position)**:
```
Hall Sensor Signal  ->  GPIO 26
Hall Sensor VCC     ->  3.3V
Hall Sensor GND     ->  Ground
```

**Inductive Sensor (Key Detection)**:
```
Inductive Signal    ->  GPIO 19
Inductive VCC       ->  3.3V
Inductive GND       ->  Ground
```

**Limit Switches**:
```
Slider MIN Signal   ->  GPIO 13
Slider MAX Signal   ->  GPIO 12
Switch VCC          ->  3.3V
Switch GND          ->  Ground
```

**Important**: All sensors should be active LOW (pull-up resistors enabled in code)

#### 6. Testing Individual Components

**Test GPIO Access**:
```bash
# Run the diagnostic script on Raspberry Pi:
python gpio_test.py
```

**Test Motor Manually**:
1. Check power supply voltage (should be 24V)
2. Verify DIP switch settings
3. Test with simple step sequence
4. Check ALM signal (should be HIGH when motor OK)

**Test Sensors**:
1. Use multimeter to check sensor outputs
2. Verify 3.3V power to sensors
3. Check signal levels (should be HIGH when inactive, LOW when active)

### Common Error Messages and Solutions

#### "ModuleNotFoundError: No module named 'RPi'"
- **Solution**: Install RPi.GPIO on Raspberry Pi, not Windows

#### "Motor Stalled!" or ALM signal LOW
- **Causes**: 
  - Insufficient power supply
  - Mechanical binding
  - Incorrect microstepping settings
  - Motor driver configuration issues
- **Solutions**:
  - Check 24V power supply
  - Verify motor can turn freely
  - Check DIP switch settings
  - Review OMC driver manual

#### "Homing failed! Hall not detected"
- **Causes**:
  - Hall sensor not wired correctly
  - Magnet not positioned properly
  - Sensor not powered
- **Solutions**:
  - Check hall sensor wiring
  - Verify magnet placement
  - Test sensor with multimeter

#### Sensors show wrong states
- **Causes**:
  - Incorrect wiring
  - Missing pull-up resistors
  - Wrong voltage levels
- **Solutions**:
  - Verify wiring against pinout
  - Check sensor power (3.3V)
  - Test with multimeter

### Step-by-Step Debugging Process

1. **Power On Test**
   - Raspberry Pi boots successfully
   - Motor driver power LED is on
   - All connections secure

2. **Software Test**
   ```bash
   python gpio_test.py
   ```
   - Should show all pins configured
   - Input pins should read HIGH (inactive)
   - Output pins should toggle

3. **Motor Test**
   - Check ALM signal (should be HIGH)
   - Send test steps manually
   - Verify motor moves

4. **Sensor Test**
   - Check each sensor individually
   - Verify active/inactive states
   - Test with actual triggers

5. **Integration Test**
   - Run homing sequence
   - Test manual movements
   - Verify sensor responses

### Emergency Procedures

**If Motor Runs Away**:
1. Disconnect power immediately
2. Check wiring for shorts
3. Verify DIP switch settings
4. Test with reduced power

**If Sensors Don't Respond**:
1. Check 3.3V power supply
2. Verify wiring connections
3. Test sensors individually
4. Check for loose connections

### Getting Help

If issues persist:
1. Document exact error messages
2. Note hardware configuration
3. Check OMC driver manual
4. Verify all connections with multimeter
5. Test components individually

### Hardware Verification Checklist

- [ ] Raspberry Pi powered and accessible
- [ ] 24V power supply connected to motor driver
- [ ] Motor driver power LED illuminated
- [ ] All GPIO connections secure
- [ ] Differential signals properly wired (+ and -)
- [ ] **Enable pins connected (EN+ to GPIO 22/25, EN- to ground)**
- [ ] **Motors can be enabled/disabled via software**
- [ ] Sensors powered with 3.3V
- [ ] DIP switches set correctly
- [ ] No loose or damaged connections
- [ ] RPi.GPIO library installed
- [ ] User has GPIO permissions
