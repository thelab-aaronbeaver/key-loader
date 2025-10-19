# Key Loader - Wiring Diagram & Ground Loop Solutions

## 🚨 **CRITICAL: Ground Loop Issues & Phantom Triggers**

Your phantom limit switch triggers are likely caused by ground loops between the Raspberry Pi and stepper motor drivers. This document provides proper wiring to eliminate these issues.

---

## 📋 **ACTUAL COMPONENTS & GPIO PIN ASSIGNMENTS**

### **Hardware Components:**
- **Raspberry Pi 4 B** - Main controller
- **DROK 48V Power Supply** - Main power (adjustable 0-48V, 10A)
- **Rotary Motor**: 23HS45-4204D-E1000 (3.0Nm Closed loop stepper)
- **Rotary Driver**: CL57T (Nema 23/24 Closed loop driver V4.1)
- **Slider Motor**: Nema 17 Pancake (1A, 17Ncm, 1.8°)
- **Slider Driver**: TB6600 (4A, 9-42V, 32 microsteps)
- **Inductive Sensor**: Taiss LJ12A3-4-Z/BX (NPN NO, DC6-36V, 4mm)
- **Hall Sensor**: HiLetgo NJK-5002C (NPN, 3-wire, NO)
- **Limit Switches**: 896F Mini Horizontal Mechanical (2x)
- **Sensor Power**: LM317 Adjustable Regulator (4.2-40V to 1.2-37V)

| Component | GPIO Pin | Function | Notes |
|-----------|----------|----------|-------|
| **Rotary Motor (CL57T)** | | | |
| STEP | 20 | Step signal (PUL+) | |
| DIR | 21 | Direction (DIR+) | |
| ENABLE | 19 | Enable/Disable (EN+) | |
| ALARM | 16 | Stall detection (ALM+) | |
| **Sensors** | | | |
| Hall Sensor | 26 | Home position (NJK-5002C) | |
| Inductive Sensor | 22 | Key detection (LJ12A3-4-Z/BX) | |
| **Slider Motor (TB6600)** | | | |
| STEP | 23 | Step signal | |
| DIR | 24 | Direction | |
| ENABLE | 25 | Enable/Disable | |
| **Limit Switches (896F)** | | | |
| Slider MIN | 27 | Inward limit | |
| Slider MAX | 17 | Outward limit | ⚠️ **UPDATED** |
| Home Switch | 5 | Legacy home (optional) | |
| End Switch | 6 | Legacy end (optional) | |

---

## 🔌 **Proper Wiring Diagram**

```
                    RASPBERRY PI 4 B
    ┌─────────────────────────────────────────────────┐
    │  GPIO 20 ──┐                                    │
    │  GPIO 21 ──┤                                    │
    │  GPIO 19 ──┤  CL57T DRIVER                      │
    │  GPIO 16 ──┤  (Rotary Motor)                    │
    │            │                                    │
    │  GPIO 23 ──┤  TB6600 DRIVER                     │
    │  GPIO 24 ──┤  (Slider Motor)                    │
    │  GPIO 25 ──┤                                    │
    │            │                                    │
    │  GPIO 26 ──┤  HALL SENSOR (NJK-5002C)          │
    │  GPIO 22 ──┤  INDUCTIVE SENSOR (LJ12A3-4-Z/BX) │
    │            │                                    │
    │  GPIO 27 ──┤  SLIDER MIN SWITCH (896F)         │
    │  GPIO 17 ──┤  SLIDER MAX SWITCH (896F)         │
    │  GPIO 5  ──┤  HOME SWITCH (optional)            │
    │  GPIO 6  ──┤  END SWITCH (optional)             │
    │            │                                    │
    │  GND ──────┼── COMMON GROUND                    │
    │  5V ───────┼── POWER FOR SENSORS                │
    │  3.3V ─────┼── LOGIC LEVEL                      │
    └─────────────────────────────────────────────────┘
                            │
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    │  CL57T DRIVER         │  TB6600 DRIVER        │
    │  (Rotary Motor)       │  (Slider Motor)       │
    │  ┌─────────────────┐  │  ┌─────────────────┐  │
    │  │ PUL+ ── GPIO 20 │  │  │ STEP ── GPIO 23 │  │
    │  │ PUL- ── GND     │  │  │ DIR ── GPIO 24  │  │
    │  │ DIR+ ── GPIO 21 │  │  │ EN ── GPIO 25   │  │
    │  │ DIR- ── GND     │  │  │ GND ── GND      │  │
    │  │ EN+ ── GPIO 19  │  │  │ VCC ── 12V      │  │
    │  │ EN- ── GND      │  │  │                 │  │
    │  │ ALM+ ── GPIO 16 │  │  │                 │  │
    │  │ ALM- ── GND     │  │  │                 │  │
    │  │ VCC ── 48V PSU  │  │  │                 │  │
    │  │ GND ── 48V PSU  │  │  │                 │  │
    │  └─────────────────┘  │  └─────────────────┘  │
    │                       │                       │
    │  NEMA 23 MOTOR        │  NEMA 17 MOTOR        │
    │  (23HS45-4204D-E1000) │  (Pancake 1A)         │
    │  ┌─────────────────┐  │  ┌─────────────────┐  │
    │  │ A+ ── CL57T     │  │  │ A+ ── TB6600    │  │
    │  │ A- ── CL57T     │  │  │ A- ── TB6600    │  │
    │  │ B+ ── CL57T     │  │  │ B+ ── TB6600    │  │
    │  │ B- ── CL57T     │  │  │ B- ── TB6600    │  │
    │  └─────────────────┘  │  └─────────────────┘  │
    └───────────────────────┼───────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    │  LIMIT SWITCHES       │  SENSORS              │
    │  (896F Mini)          │  (Powered by LM317)   │
    │  ┌─────────────────┐  │  ┌─────────────────┐  │
    │  │ MIN ── GPIO 27  │  │  │ HALL ── GPIO 26 │  │
    │  │ MAX ── GPIO 17  │  │  │ IND ── GPIO 22  │  │
    │  │ COM ── GND      │  │  │ VCC ── LM317    │  │
    │  │ NO ── 5V        │  │  │ GND ── GND      │  │
    │  └─────────────────┘  │  └─────────────────┘  │
    └───────────────────────┼───────────────────────┘
                            │
                    ⚡ COMMON GROUND ⚡
```

---

## ⚙️ **COMPONENT-SPECIFIC CONFIGURATIONS**

### **DROK 48V Power Supply Setup:**
```
DROK 48V Supply Outputs:
├── 48V ── CL57T Driver (Rotary Motor)
├── 24V ── TB6600 Driver (Slider Motor) 
├── 12V ── LM317 Regulator Input
├── 5V ── Raspberry Pi + Sensors
└── GND ── Common Ground (ALL components)
```

### **CL57T Driver (Rotary Motor) Configuration:**
- **Power**: 48V from DROK supply
- **Microstepping**: 16x (3200 steps/revolution) - **CORRECTED**
- **Current**: Set for 3.0Nm motor (typically 2.5-3.0A)
- **Enable Logic**: LOW = enabled, HIGH = disabled
- **Alarm Logic**: HIGH = OK, LOW = fault

### **TB6600 Driver (Slider Motor) Configuration:**
- **Power**: 24V from DROK supply  
- **Microstepping**: 8x (1600 steps/revolution) - **UPDATED**
- **Current**: Set for 1A motor (typically 0.8-1.0A)
- **Enable Logic**: LOW = enabled, HIGH = disabled

### **Sensor Power (LM317 Regulator):**
```
Input: 12V from DROK supply
Output: 5V for sensors
Components powered:
├── Hall Sensor (NJK-5002C)
├── Inductive Sensor (LJ12A3-4-Z/BX)
└── Limit Switches (896F)
```

### **896F Limit Switch Wiring:**
```
896F Switch Connections:
├── COM ── GPIO Pin (27 or 17)
├── NO ── 5V (from LM317)
└── NC ── Not used
```

---

## ⚠️ **GROUND LOOP SOLUTIONS**

### **Problem: Phantom Limit Switch Triggers**
- **CL57T (48V) + TB6600 (24V)** create different ground potentials
- **DROK 48V supply** can create switching noise
- **896F mechanical switches** are sensitive to electrical noise
- **Shared ground paths** cause voltage fluctuations
- **GPIO pins** read false HIGH/LOW states during motor acceleration

### **Solution 1: Isolated Ground Planes**
```
RASPBERRY PI GROUND ──┐
                      │
MOTOR DRIVER GROUND ──┼── COMMON CHASSIS GROUND
                      │
SENSOR GROUND ────────┘
```

### **Solution 2: Optocoupler Isolation (RECOMMENDED)**
```
LIMIT SWITCH ──┐
               │
               │  ┌─────────────┐
               └──┤ OPTOCOUPLER ├── GPIO PIN
                   │  (4N35)     │
                   └─────────────┘
```

### **Solution 3: Pull-up Resistors**
```
5V ──┬── 10kΩ ──┬── GPIO PIN
     │          │
     │          └── LIMIT SWITCH ── GND
     │
     └── 0.1μF CAPACITOR ── GND (NOISE FILTER)
```

---

## 🔧 **IMMEDIATE FIXES**

### **1. Add Pull-up Resistors**
```python
# In hardware_controller.py - already implemented
GPIO.setup(self.SLIDER_MIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(self.SLIDER_MAX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
```

### **2. Add Debouncing**
```python
def read_slider_min_debounced(self):
    """Read MIN switch with debouncing to prevent phantom triggers."""
    readings = []
    for _ in range(5):  # Take 5 readings
        readings.append(GPIO.input(self.SLIDER_MIN_PIN) == GPIO.LOW)
        time.sleep(0.001)  # 1ms delay
    
    # Return True only if majority of readings are True
    return sum(readings) >= 3

def read_slider_max_debounced(self):
    """Read MAX switch with debouncing to prevent phantom triggers."""
    readings = []
    for _ in range(5):  # Take 5 readings
        readings.append(GPIO.input(self.SLIDER_MAX_PIN) == GPIO.LOW)
        time.sleep(0.001)  # 1ms delay
    
    # Return True only if majority of readings are True
    return sum(readings) >= 3
```

### **3. Separate Power Supplies**
- **Raspberry Pi**: Use dedicated 5V/3A supply
- **TB6600**: Use dedicated 24V supply
- **Slider Driver**: Use separate 12V/24V supply
- **Common Ground**: Connect all grounds at ONE point only

---

## 🛠️ **HARDWARE MODIFICATIONS**

### **Option A: Optocoupler Board (Best Solution)**
```
Component List:
- 4x 4N35 Optocouplers
- 4x 220Ω Resistors (for LED side)
- 4x 10kΩ Resistors (for transistor side)
- 1x Perfboard or PCB
```

### **Option B: RC Filter (Quick Fix)**
```
Each limit switch input:
GPIO ── 1kΩ ──┬── 0.1μF ── GND
              │
              └── LIMIT SWITCH
```

### **Option C: Ferrite Beads**
```
Motor power cables:
24V+ ── FERRITE BEAD ── TB6600 VCC
24V- ── FERRITE BEAD ── TB660O GND
```

---

## 📊 **TESTING PROCEDURE**

### **1. Test Individual Components**
```bash
# Test limit switches without motors running
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for i in range(10):
    min_state = GPIO.input(27)
    max_state = GPIO.input(17)
    print(f'MIN: {min_state}, MAX: {max_state}')
    time.sleep(0.1)
"
```

### **2. Test With Motors Running**
- Run slider test cycle
- Monitor console output for phantom triggers
- Check if triggers occur during motor acceleration

### **3. Oscilloscope Analysis**
- Monitor GPIO pins during motor operation
- Look for voltage spikes or noise
- Measure ground potential differences

---

## 🚨 **EMERGENCY WORKAROUND**

If phantom triggers persist, add this temporary fix to your code:

```python
def is_phantom_trigger(self, pin):
    """Detect if a trigger is likely phantom based on timing."""
    # If trigger occurs during motor acceleration, it's likely phantom
    if self.motor_accelerating:
        return True
    
    # If trigger duration is very short (< 10ms), it's likely phantom
    start_time = time.time()
    while GPIO.input(pin) == GPIO.LOW:
        if time.time() - start_time > 0.01:  # 10ms
            return False  # Real trigger
    return True  # Phantom trigger
```

---

## 📞 **SUPPORT**

If issues persist after implementing these solutions:
1. Check all ground connections with multimeter
2. Verify power supply isolation
3. Consider professional EMI/EMC analysis
4. Implement optocoupler isolation as final solution

**Remember**: Ground loops are the #1 cause of phantom limit switch triggers in stepper motor systems!
