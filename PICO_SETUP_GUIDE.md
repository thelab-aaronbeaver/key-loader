# Raspberry Pico Keyboard Emulator Setup Guide

## 🎯 **Overview**
This guide sets up a Raspberry Pico to receive GPIO triggers from your main Raspberry Pi and emulate pressing the Enter key on a keyboard.

## 📋 **Required Components**
- Raspberry Pico (or Pico W)
- USB cable (for programming and power)
- Jumper wires for GPIO connection
- Computer with CircuitPython support

## 🔧 **Setup Steps**

### **Step 1: Install CircuitPython on Pico**
1. Download CircuitPython for Pico from: https://circuitpython.org/board/raspberry_pi_pico/
2. Hold BOOTSEL button on Pico while connecting USB
3. Drag the downloaded `.uf2` file to the mounted drive
4. Pico will reboot and show as `CIRCUITPY` drive

### **Step 2: Install Required Libraries**
1. Download `adafruit-circuitpython-hid` from: https://github.com/adafruit/Adafruit_CircuitPython_HID
2. Copy the `adafruit_hid` folder to your Pico's `lib` folder
3. Your Pico should now have:
   ```
   CIRCUITPY/
   ├── lib/
   │   └── adafruit_hid/
   └── code.py
   ```

### **Step 3: Upload the Code**
1. Copy `pico_keyboard_trigger.py` to your Pico
2. Rename it to `code.py` (this makes it run automatically)
3. Your Pico will now act as a keyboard emulator

### **Step 4: Wiring Connection**
```
Raspberry Pi 4          Raspberry Pico
┌─────────────┐         ┌─────────────┐
│ GPIO 4 ─────┼─────────┤ GPIO 2      │
│ GND ────────┼─────────┤ GND         │
│ 3.3V ───────┼─────────┤ 3.3V        │
└─────────────┘         └─────────────┘
```

**Note**: You can change the trigger pin in the code by modifying `TRIGGER_PIN = 2` to any available GPIO pin.

## 🎮 **How It Works**

1. **Trigger Detection**: Pico monitors GPIO 2 for HIGH signal
2. **Key Press**: When triggered, Pico emulates pressing Enter key
3. **Visual Feedback**: Built-in LED blinks to show activity
4. **USB HID**: Pico appears as a keyboard to your computer

## 🔍 **Testing**

### **Test 1: Manual Trigger**
1. Connect a jumper wire from 3.3V to GPIO 2 on Pico
2. LED should blink and Enter key should be pressed
3. Remove wire to stop

### **Test 2: Pi Integration**
1. Run your main key loader application
2. When a key is detected, the Pi will trigger GPIO 4
3. Pico should receive the signal and press Enter

### **Test 3: GPIO Test Tool**
1. Run `python gpio_test.py` on your Pi
2. The Pico trigger test will send pulses
3. Pico should respond with Enter key presses

## ⚙️ **Configuration Options**

### **Change Trigger Pin**
```python
# In pico_keyboard_trigger.py, change this line:
TRIGGER_PIN = 2  # Change to any GPIO pin (0-28)
```

### **Change Key Press**
```python
# To press a different key, modify press_enter_key():
keyboard.press(Keycode.SPACE)  # Press Space instead
keyboard.press(Keycode.TAB)    # Press Tab instead
keyboard.press(Keycode.ESCAPE) # Press Escape instead
```

### **Press Multiple Keys**
```python
# To press Ctrl+C:
keyboard.press(Keycode.CONTROL, Keycode.C)
keyboard.release_all()

# To press Alt+F4:
keyboard.press(Keycode.ALT, Keycode.F4)
keyboard.release_all()
```

## 🐛 **Troubleshooting**

### **Pico Not Detected as Keyboard**
- Check that CircuitPython is properly installed
- Verify `adafruit_hid` library is in the `lib` folder
- Try unplugging and reconnecting USB

### **No Response to Triggers**
- Check wiring between Pi and Pico
- Verify GPIO pin numbers match
- Test with manual 3.3V connection to trigger pin

### **Multiple Key Presses**
- Increase the delay in `check_trigger()` function
- Add debouncing logic if needed

### **LED Not Blinking**
- Check that GPIO 25 is available (built-in LED)
- Modify LED pin if using external LED

## 📝 **Code Customization**

### **Add More Functions**
```python
def press_space_key():
    """Press Space key instead of Enter"""
    keyboard.press(Keycode.SPACE)
    time.sleep(0.05)
    keyboard.release(Keycode.SPACE)

def press_tab_key():
    """Press Tab key"""
    keyboard.press(Keycode.TAB)
    time.sleep(0.05)
    keyboard.release(Keycode.TAB)
```

### **Add Multiple Trigger Pins**
```python
# Add more trigger pins for different functions
TRIGGER_PIN_1 = 2  # Enter key
TRIGGER_PIN_2 = 3  # Space key
TRIGGER_PIN_3 = 4  # Tab key

trigger_pin_1 = machine.Pin(TRIGGER_PIN_1, machine.Pin.IN, machine.Pin.PULL_DOWN)
trigger_pin_2 = machine.Pin(TRIGGER_PIN_2, machine.Pin.IN, machine.Pin.PULL_DOWN)
trigger_pin_3 = machine.Pin(TRIGGER_PIN_3, machine.Pin.IN, machine.Pin.PULL_DOWN)
```

## 🔒 **Security Note**
This Pico will act as a keyboard and can send any keystrokes to your computer. Only use it in trusted environments and ensure the code is secure.

## 📚 **Additional Resources**
- [CircuitPython Documentation](https://docs.circuitpython.org/)
- [Adafruit HID Library](https://github.com/adafruit/Adafruit_CircuitPython_HID)
- [Raspberry Pico Pinout](https://datasheets.raspberrypi.org/pico/Pico-R3-A4-Pinout.pdf)
