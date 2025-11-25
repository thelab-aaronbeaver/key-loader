# Inductive Sensor Voltage Fix Guide

## 🔍 Your Current Problem:
- **No metal**: 0.7V (too low, should be ~3.0V)
- **Metal detected**: 0.3V (acceptable LOW, but should be closer to 0V)

## ⚡ Root Cause:
Your voltage divider circuit isn't working correctly. The LJ12A3-4-Z/BX sensor outputs:
- **Active (metal detected)**: ~0V (connects to GND)
- **Inactive (no metal)**: OPEN CIRCUIT (not 12V!)

**NPN NO (Normally Open)** sensors need a **pull-up resistor** to 12V, not just a voltage divider!

---

## ✅ SOLUTION 1: Proper Wiring with Pull-up (RECOMMENDED)

### Circuit Diagram:
```
        +12V (from LM317 or sensor power)
         │
         ├─── 10kΩ (Pull-up resistor) ───┐
         │                                │
         │                          SENSOR OUTPUT
         │                                │
         │                                ├─── 10kΩ ──┬─── GPIO 22
         │                                │            │
         │                                │        3.3kΩ
         │                                │            │
        GND ──────────────────────────────┴────────────┴─── GND
```

### What You Need:
1. **Add 10kΩ pull-up resistor** from sensor output to +12V
2. Keep existing voltage divider (10kΩ + 3.3kΩ)

### Why This Works:
- Pull-up resistor brings sensor output to 12V when inactive
- When active, sensor pulls output to GND
- Voltage divider drops 12V → 3.0V for GPIO
- When active, 0V stays 0V through divider

---

## ✅ SOLUTION 2: Simplified Circuit (EASIER)

If you don't want to add a pull-up to 12V, use the Pi's internal pull-up:

### Circuit:
```
    SENSOR OUTPUT ───┬─── GPIO 22 (with internal pull-up)
                     │
                    GND
```

### Configuration:
- **Remove voltage divider completely**
- Connect sensor output directly to GPIO 22
- Sensor brown wire → 12V
- Sensor blue wire → GND  
- Sensor black wire → GPIO 22
- Use Pi's internal pull-up resistor

### Trade-off:
- ⚠️ **DANGER**: If sensor malfunctions and outputs 12V, it will **DESTROY the Pi!**
- Only safe because NPN NO sensors NEVER output voltage, only GND
- Pi's internal pull-up (to 3.3V) will keep pin HIGH when inactive

---

## ✅ SOLUTION 3: Try Inverted Logic (SOFTWARE FIX)

If you can't change wiring right now, try inverted logic:

Your current readings suggest it might work if we flip the logic:
- 0.7V might register as HIGH on GPIO (threshold is ~0.5-0.8V)
- 0.3V will register as LOW

We can invert the reading in software.

---

## 🔧 SOLUTION 4: Better Voltage Divider Values

If you want to keep the voltage divider approach but get better voltages:

### For 12V input → 3.0V output:
- **R1 = 27kΩ** (from sensor to GPIO)
- **R2 = 9.1kΩ** (from GPIO to GND)
- Formula: Vout = 12V × (9.1kΩ / (27kΩ + 9.1kΩ)) = 3.02V

### But you still need the pull-up resistor!
Add **10kΩ from sensor output to +12V**

---

## 🎯 RECOMMENDED ACTION:

### Quick Test (No Hardware Changes):
Try the direct connection (Solution 2) temporarily to test:
1. Disconnect voltage divider
2. Connect sensor output directly to GPIO 22
3. Sensor should work immediately

### Permanent Fix (Best):
Implement Solution 1:
1. Add 10kΩ pull-up from sensor output to +12V
2. Keep or replace voltage divider as needed
3. This is industry-standard for NPN sensors

### Emergency Software Fix:
If you can't change hardware, I can modify the code to work with your current setup by:
1. Using internal pull-down instead of pull-up
2. Inverting the logic in software
3. Adding debouncing for unstable readings

---

## 📊 Testing Your Fix:

Run this command to test voltages:
```bash
# Measure with multimeter:
# Pin 1: Sensor output (before voltage divider)
# Pin 2: GPIO 22 (after voltage divider)

# Expected values with pull-up:
No metal:  Sensor=12V, GPIO=3.0V
Metal:     Sensor=0V,  GPIO=0V
```

Let me know which solution you want to try!

