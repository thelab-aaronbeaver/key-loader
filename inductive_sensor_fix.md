# Inductive Sensor Voltage Fix Guide

## ⚡ QUICK TEMPORARY FIX (Software Only):

**Current Status:** Code now uses Pi's internal pull-up resistor.

This will work temporarily:
- **No metal**: Internal pull-up brings GPIO to 3.3V (HIGH)
- **Metal detected**: Sensor pulls GPIO to GND/0V (LOW)

**Test it now:**
```bash
sudo python3 gpio_test.py
```

The sensor should work! But for production reliability, add an external pull-up (see below).

---

## 🔍 Your Current Problem (Hardware):
- **No metal**: 0.3V (way too low!)
- **Metal detected**: 0.025V (good, basically 0V/GND)

## ⚡ Root Cause:
**Both voltages read as LOW on the GPIO!** You can't distinguish between states.

The LJ12A3-4-Z/BX is an **NPN NO (Normally Open)** sensor, which means:
- **Active (metal detected)**: Output connects to GND → ~0V ✅ (working correctly!)
- **Inactive (no metal)**: Output is **OPEN CIRCUIT** (floating) → Leaking 0.3V ❌

**The sensor output NEVER provides voltage!** It only:
1. **Floats** (open circuit) when inactive
2. **Connects to GND** when active

You **MUST** add a pull-up resistor to bring the floating state to a HIGH voltage!

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

## ✅ SOLUTION 2: Pi Internal Pull-up (CURRENT - TEMPORARY)

**This is what the code is using now!**

### Circuit:
```
    SENSOR OUTPUT (black) ─── GPIO 22 (with internal pull-up to 3.3V)
                         
    SENSOR POWER (brown) ─── +12V
    SENSOR GND (blue) ─────── GND
```

### How It Works:
- **Remove any voltage divider** between sensor and GPIO 22
- Connect sensor output (black wire) **directly** to GPIO 22
- Pi's internal ~50kΩ pull-up brings pin to 3.3V when sensor is floating
- When sensor detects metal, it pulls pin to GND

### Current Behavior:
- **No metal**: Sensor floating (0.3V external) → Internal pull-up makes GPIO read 3.3V (HIGH)
- **Metal**: Sensor connects to GND (0.025V) → GPIO reads 0V (LOW)

### Trade-offs:
- ✅ **Works immediately** with no hardware changes
- ✅ **Safe** - NPN NO sensors never output voltage, only connect to GND
- ⚠️ **Weak pull-up** - 50kΩ internal resistor may pick up noise
- ⚠️ **Not production-grade** - Better to use external pull-up

### When to Use:
- Testing/debugging
- Temporary operation while waiting for parts
- Low-noise environments

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

