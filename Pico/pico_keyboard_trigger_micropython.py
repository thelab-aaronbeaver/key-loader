#!/usr/bin/env python3
"""
Raspberry Pico Keyboard Emulator (MicroPython Version)
Receives GPIO trigger from Raspberry Pi and emulates Enter key press
Note: This version requires custom HID implementation for MicroPython
"""

import machine
import time

# Configure trigger pin (adjust pin number to match your wiring)
TRIGGER_PIN = 2

# Configure trigger pin as input with pull-down resistor
trigger_pin = machine.Pin(TRIGGER_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)

# LED for visual feedback (built-in LED on GPIO 25)
led = machine.Pin(25, machine.Pin.OUT)

def blink_led(times=3, delay=0.1):
    """Blink LED for visual feedback"""
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

def send_enter_key():
    """Send Enter key via USB HID (MicroPython implementation)"""
    print("🎹 Sending Enter key...")
    
    # Visual feedback
    blink_led(2, 0.05)
    
    # Note: This is a placeholder - actual HID implementation would go here
    # For MicroPython, you'd need to implement USB HID manually or use
    # a library like micropython-adafruit-hid
    
    print("✅ Enter key sent!")
    print("⚠️  Note: This is a placeholder - implement actual HID for MicroPython")

def check_trigger():
    """Check for trigger signal from Raspberry Pi"""
    if trigger_pin.value() == 1:
        print("📡 Trigger received from Pi!")
        send_enter_key()
        return True
    return False

def main():
    """Main program loop"""
    print("🚀 Pico Keyboard Emulator Started (MicroPython)")
    print(f"📌 Listening for triggers on GPIO {TRIGGER_PIN}")
    print("🎹 Will send Enter key when triggered")
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
