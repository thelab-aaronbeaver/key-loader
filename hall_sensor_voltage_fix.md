# Hall Sensor Voltage Fix - URGENT

## 🚨 CRITICAL WARNING!

Your Hall sensor is reading:
- **5V with no magnet** (idle)
- **0.05V with magnet** (active)

**5V is ABOVE the 3.3V maximum for Raspberry Pi GPIO!**

This can **damage your Pi** over time. You need to add a voltage divider **immediately**.

---

## 🎯 QUICK FIX - Add Voltage Divider

### What You Need:
- **One 10kΩ resistor**
- **One 6.8kΩ resistor** (or 6.2kΩ, or two 3.3kΩ in series)

### Circuit:
```
Hall Sensor Output (5V) ─── 10kΩ ───┬─── GPIO 27 (~3.0V)
                                     │
                                   6.8kΩ
                                     │
                                    GND
```

### How It Works:
Voltage divider formula: Vout = Vin × (R2 / (R1 + R2))
- Vout = 5V × (6.8kΩ / (10kΩ + 6.8kΩ))
- Vout = 5V × (6.8 / 16.8) = **3.0V** ✅ Safe for GPIO!

When magnet detected (0.05V input):
- Vout = 0.05V × (6.8 / 16.8) = **0.02V** ✅ Still reads as LOW

---

## 📋 Step-by-Step Fix:

### Step 1: Disconnect Hall Sensor
1. Turn off power to Pi
2. Disconnect Hall sensor output wire from GPIO 27

### Step 2: Build Voltage Divider
```
Hall Sensor Wire (currently showing 5V)
    │
    └─── 10kΩ resistor ───┬─── to GPIO 27
                          │
                        6.8kΩ resistor
                          │
                         GND
```

### Step 3: Physical Wiring
1. **10kΩ resistor**: One leg to Hall sensor wire, other leg to GPIO 27
2. **6.8kΩ resistor**: One leg to GPIO 27, other leg to GND
3. The junction point (between resistors) connects to GPIO 27

### Step 4: Verify Voltages
Measure with multimeter at GPIO 27:
- **No magnet**: Should read **~3.0V** (was 5V) ✅
- **Magnet near**: Should read **~0V** (was 0.05V) ✅

---

## 🔧 Alternative Resistor Values:

If you don't have exactly 6.8kΩ, use these combinations:

### Option 1: 10kΩ + 6.8kΩ (ideal)
- Vout = 3.0V ✅

### Option 2: 10kΩ + 6.2kΩ
- Vout = 5V × (6.2/16.2) = 3.1V ✅

### Option 3: 10kΩ + two 3.3kΩ in series (6.6kΩ total)
- Vout = 5V × (6.6/16.6) = 3.0V ✅

### Option 4: 10kΩ + 5.6kΩ
- Vout = 5V × (5.6/15.6) = 2.9V ✅

### Option 5: 10kΩ + 10kΩ (if nothing else available)
- Vout = 5V × (10/20) = 2.5V ✅ (works, but lower signal)

**Any of these work! Use what you have.**

---

## 🔍 Why Is Your Hall Sensor Outputting 5V?

### Possible Reasons:

1. **Sensor is powered by 5V instead of 12V**
   - Check sensor power wire (brown): Should it be 12V?
   - If powered by 5V, it outputs 5V when active

2. **Sensor has internal pull-up to its power voltage**
   - Hall sensor might have internal pull-up
   - When idle, output = power voltage

3. **LM317 regulator set to 5V instead of 12V**
   - Check your LM317 output voltage
   - Should be set for sensor power (typically 5-12V)

### To Check:
```bash
# Measure Hall sensor power input (brown wire):
# If 5V: That's why output is 5V (normal behavior)
# If 12V: Sensor should output 12V (needs different voltage divider)
```

---

## 🎯 If Hall Sensor is Powered by 12V:

If you measure 12V on the brown wire but still see 5V output:
- There might be regulation happening
- Check if there's already a voltage divider in your circuit

If powered by 12V and outputting 12V (not 5V):
Use different resistor values:
- **27kΩ + 10kΩ**: 12V → 3.2V
- **33kΩ + 10kΩ**: 12V → 2.8V
- **Or use the original 10kΩ + 3.3kΩ from wiring diagram**: 12V → 3.0V

---

## ⚡ Emergency Temporary Fix:

If you can't add resistors right now, you can use a **software workaround**:

The Hall sensor IS working (5V idle, 0.05V active). Both are readable by GPIO:
- 5V reads as HIGH (though risky for Pi!)
- 0.05V reads as LOW

**Current code should work**, but **DON'T leave it this way** - add voltage divider ASAP!

---

## 📊 Testing After Fix:

```bash
sudo python3 gpio_test.py
```

The sensor reading test should show:
- Hall sensor toggles between ACTIVE and INACTIVE when you move magnet

---

## 🔌 Complete Safe Wiring:

### Hall Sensor (NJK-5002C):
```
Sensor Brown (power) ─── +5V or +12V supply
Sensor Blue (ground) ─── GND
Sensor Black (signal) ─── 10kΩ ───┬─── GPIO 27
                                   │
                                 6.8kΩ (or appropriate value)
                                   │
                                  GND
```

### Inductive Sensor (LJ12A3-4-Z/BX):
```
Sensor Brown (power) ─── +12V supply
Sensor Blue (ground) ─── GND
Sensor Black (signal) ─── GPIO 22
                           │
Pi 3.3V ─── 4.7kΩ ─────────┘
```

---

## 💡 Summary:

1. ⚠️ **5V at GPIO 27 is dangerous** - exceeds 3.3V max
2. ✅ **Add voltage divider** (10kΩ + 6.8kΩ) to drop 5V → 3.0V
3. ✅ **Hall sensor IS working** - just needs voltage scaling
4. 📖 **See quick_sensor_fix.md** for inductive sensor wiring

Both sensors are functioning correctly, they just need proper voltage level conversion!

