#!/usr/bin/env python3
"""
Raspberry Pico Keyboard Emulator
Receives GPIO trigger from Raspberry Pi and emulates Enter key press
"""

import machine
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# Configure trigger pin (adjust pin number to match your wiring)
# GPIO 2 is commonly used, but change to match your connection
TRIGGER_PIN = 2

# Configure trigger pin as input with pull-down resistor
trigger_pin = machine.Pin(TRIGGER_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Initialize USB HID keyboard
keyboard = Keyboard(usb_hid.devices)

# LED for visual feedback (optional - built-in LED on GPIO 25)
led = machine.Pin(25, machine.Pin.OUT)

def blink_led(times=3, delay=0.1):
    """Blink LED for visual feedback"""
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

def press_enter_key():
    """Emulate pressing the Enter key"""
    print("🎹 Pressing Enter key...")
    
    # Visual feedback
    blink_led(2, 0.05)
    
    # Press and release Enter key
    keyboard.press(Keycode.ENTER)
    time.sleep(0.05)  # Hold for 50ms
    keyboard.release(Keycode.ENTER)
    
    print("✅ Enter key pressed!")

def check_trigger():
    """Check for trigger signal from Raspberry Pi"""
    if trigger_pin.value() == 1:
        print("📡 Trigger received from Pi!")
        press_enter_key()
        return True
    return False

def main():
    """Main program loop"""
    print("🚀 Pico Keyboard Emulator Started")
    print(f"📌 Listening for triggers on GPIO {TRIGGER_PIN}")
    print("🎹 Will press Enter key when triggered")
    print("⏹️  Press Ctrl+C to stop")
    
    # Initial LED blink to show startup
    blink_led(5, 0.1)
    
    try:
        while True:
            # Check for trigger signal
            if check_trigger():
                # Small delay to prevent multiple triggers from same pulse
                time.sleep(0.2)
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)  # Check every 10ms
            
    except KeyboardInterrupt:
        print("\n⏹️  Program stopped by user")
        led.off()
    except Exception as e:
        print(f"❌ Error: {e}")
        led.off()

if __name__ == "__main__":
    main()
