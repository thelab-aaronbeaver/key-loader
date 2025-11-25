# Inductive Sensor Voltage Fix Guide

## ⚡ CURRENT STATUS - NOT WORKING:

**Problem:** Pi's internal pull-up is TOO WEAK (50kΩ)
- Current readings: 0.5V (idle) / 0.09V (active)
- Both read as LOW - can't distinguish!
- Sensor has 300Ω internal resistor that loads down the weak pull-up

**You MUST add an external pull-up resistor!**

---

## 🎯 IMMEDIATE FIX - Add External Pull-up to 3.3V

### What You Need:
- **One 4.7kΩ resistor** (or 3.3kΩ to 10kΩ range)

### Wiring (REMOVE voltage divider if present):
```
Pi 3.3V Pin ─── 4.7kΩ resistor ─── Sensor Output (black) ─── GPIO 22

Sensor Brown (power) ─── +12V
Sensor Blue (ground) ──── GND
```

### Why 3.3V Instead of 12V:
- Safe for Pi (no risk of overvoltage)
- Strong enough to overcome sensor's 300Ω internal resistor
- Direct connection, no voltage divider needed

### Expected Results:
- **No metal**: Resistor pulls GPIO to 3.3V (HIGH)
- **Metal**: Sensor's 300Ω pulls to GND (LOW)
- Voltage divider: 3.3V × (300 / (4700 + 300)) = 0.2V (LOW) ✅

---

## 🔍 Diagnostic - Check Your Current Wiring:

### Current Readings:
- **No metal**: 0.5V (too low!)
- **Metal detected**: 0.09V (too low!)

### What's Wrong:
Both voltages are **below GPIO threshold (~0.8V)**, so both read as LOW.

### Likely Issues:
1. ❌ **Voltage divider still connected?** (10kΩ + 3.3kΩ resistors)
2. ❌ **Pi's internal pull-up too weak** (50kΩ can't overcome 300Ω sensor)
3. ❌ **No external pull-up resistor**

### Check Your Wiring Now:
1. Measure voltage **directly at sensor output** (black wire):
   - Should be close to 12V when idle (if external pull-up to 12V)
   - Should be close to 3.3V when idle (if pull-up to 3.3V)
   - Should be close to 0V when active
2. Check if there are resistors between sensor and GPIO 22
3. If voltage divider present, remove it

---

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

## ✅ SOLUTION 1: Pull-up to 3.3V (EASIEST - RECOMMENDED)

### Circuit Diagram:
```
    Raspberry Pi
    ┌─────────────┐
    │ 3.3V Pin ───┼─── 4.7kΩ ───┬─── Sensor Black (output)
    │             │              │
    │ GPIO 22 ────┼──────────────┘
    │             │
    │ GND ────────┼─── Sensor Blue (GND)
    └─────────────┘

    +12V Supply ─── Sensor Brown (power)
```

### Step-by-Step:
1. **Disconnect sensor from GPIO 22**
2. **Remove any voltage divider** (10kΩ/3.3kΩ resistors) if present
3. **Connect directly:**
   - Sensor black wire → GPIO 22
   - 4.7kΩ resistor between Pi's 3.3V pin and sensor black wire
4. **Power connections stay the same:**
   - Sensor brown → +12V
   - Sensor blue → GND

### Expected Voltages:
- **No metal**: 3.3V on GPIO (HIGH) ✅
- **Metal**: 0.2V on GPIO (LOW) ✅

### Why This Works:
- 4.7kΩ is strong enough to pull up against sensor's 300Ω internal resistor
- When sensor activates, 300Ω to GND creates voltage divider: 3.3V × (300/(4700+300)) = 0.2V
- Safe for Pi - no risk of overvoltage since pull-up is to 3.3V, not 12V

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

## ✅ SOLUTION 3: Pull-up to 5V (Alternative)

If you don't have 3.3V available at your mounting location:

### Circuit:
```
    Pi 5V Pin ─── 10kΩ ───┬─── Sensor Black (output)
                          │
    Pi GPIO 22 ───────────┴─── 10kΩ ─── GND
```

### This Creates Voltage Divider:
- **No metal**: 5V pulled through 10kΩ, divided to 2.5V (HIGH) ✅
- **Metal**: Sensor's 300Ω pulls low, ~0.15V (LOW) ✅

### Trade-off:
- More components (2 resistors)
- But safer if sensor ever outputs voltage

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

