# Quick Inductive Sensor Fix - Step by Step

## 🚨 CURRENT PROBLEM:
Your sensor reads:
- **0.5V when idle** (should be 3.3V)
- **0.09V when active** (this is OK)
- **Both read as LOW on GPIO - CAN'T DETECT!**

---

## 🎯 5-MINUTE FIX:

### What You Need:
- **One 4.7kΩ resistor** (or anything from 3.3kΩ to 10kΩ)
- If you don't have 4.7kΩ, you can use:
  - 3.3kΩ (will work)
  - 5.6kΩ (will work)
  - 10kΩ (will work)

### Step 1: Disconnect Current Wiring
1. Turn off power
2. Disconnect the sensor's black wire from GPIO 22
3. **Check if there are any resistors between sensor and GPIO**
   - If YES: Remove them (you may have a voltage divider)

### Step 2: New Simple Wiring
Connect exactly this way:

```
┌─────────────────────────────────────────────────┐
│  Raspberry Pi                                   │
│                                                 │
│  Pin 1 (3.3V) ───────┐                         │
│                      │                         │
│                   4.7kΩ resistor               │
│                      │                         │
│  GPIO 22 ────────────┴───── Sensor Black Wire  │
│                                                 │
│  GND ──────────────────────── Sensor Blue Wire  │
│                                                 │
└─────────────────────────────────────────────────┘

    +12V Supply ──────────────── Sensor Brown Wire
```

### Step 3: Physical Connections
1. **Sensor Brown (power)** → +12V power supply (unchanged)
2. **Sensor Blue (ground)** → Raspberry Pi GND (unchanged)
3. **Sensor Black (signal)** → GPIO 22 on Pi
4. **4.7kΩ resistor** → Between Pi's 3.3V pin and sensor black wire

### Step 4: Test
```bash
sudo python3 gpio_test.py
```

---

## 📊 What Should Happen:

### Before Fix (Current):
```
Measure at GPIO 22:
- No metal: 0.5V  ← reads as LOW ❌
- Metal:    0.09V ← reads as LOW ❌
BOTH LOW = CAN'T DETECT!
```

### After Fix:
```
Measure at GPIO 22:
- No metal: 3.3V  ← reads as HIGH ✅
- Metal:    0.2V  ← reads as LOW ✅
CAN DETECT!
```

---

## 🔧 Which Resistor Value to Use?

### Calculation:
When sensor activates (300Ω to GND), voltage at GPIO:
- **With 3.3kΩ**: 3.3V × (300/3600) = 0.27V (LOW) ✅
- **With 4.7kΩ**: 3.3V × (300/5000) = 0.20V (LOW) ✅
- **With 10kΩ**: 3.3V × (300/10300) = 0.10V (LOW) ✅

**All work fine!** Use whatever you have.

---

## 🚨 Common Mistakes to Avoid:

1. ❌ **Don't use Pi's 5V pin** - Risk of overvoltage if sensor malfunctions
2. ❌ **Don't keep old voltage divider** - Remove those 10kΩ/3.3kΩ resistors
3. ❌ **Don't use resistor > 47kΩ** - Won't pull up strong enough
4. ❌ **Don't connect to 12V** - Needs voltage divider (more complex)

---

## 📍 Finding Pi's 3.3V Pin:

Raspberry Pi 4 Header (looking at board with USB ports at bottom):

```
     3.3V → ● ○  ← 5V
            ● ○
            ○ ○
            ○ ○
     GND  → ● ○
            ○ ○
            ● ○  ← GPIO 22 (Pin 15)
            ...
```

- **Pin 1 (top left)**: 3.3V
- **Pin 6 (3rd row left)**: GND  
- **Pin 15 (8th row left)**: GPIO 22

---

## ✅ Verification:

After wiring, measure with multimeter:
1. **Measure at GPIO 22** (with no metal near sensor):
   - Should read **~3.0V to 3.3V** ✅
2. **Bring metal close** to sensor:
   - Should drop to **~0.1V to 0.3V** ✅
3. **If correct**, run the test:
   ```bash
   sudo python3 gpio_test.py
   ```

---

## 💡 If Still Not Working:

### Check sensor power:
```bash
# Measure sensor brown wire: should be 12V
# Measure sensor blue wire: should be 0V (GND)
```

### Check sensor output:
```bash
# Measure sensor black wire BEFORE adding pull-up:
# - Should be ~0.3V to 0.5V (floating)
# After adding 4.7kΩ to 3.3V:
# - Should be 3.3V (idle) or 0.2V (active)
```

### Test sensor separately:
```bash
# Connect sensor black wire to multimeter positive
# Connect multimeter negative to GND
# Should show:
#   - Near 0V normally
#   - Exact 0V when metal close (if sensor working)
```

---

## 🎯 Why This Works:

Your sensor has a **300Ω internal resistor** and is **NPN NO** type:
- **Inactive**: Output is **open circuit** (floating)
- **Active**: Output **connects to GND through 300Ω**

Without pull-up:
- Floating output picks up noise → 0.5V (random!)
- Can't reach logic HIGH

With 4.7kΩ pull-up to 3.3V:
- Pull-up brings floating output to 3.3V ✅
- When active, 300Ω and 4.7kΩ form voltage divider → 0.2V ✅

**Now GPIO can detect both states!**

