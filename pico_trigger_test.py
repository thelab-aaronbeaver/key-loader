# trigger_script_for_pi4.py
import RPi.GPIO as GPIO
import time

# Use Broadcom pin numbering
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up GPIO 4 as an output pin
TRIGGER_PIN = 4
GPIO.setup(TRIGGER_PIN, GPIO.OUT)

def send_trigger():
    """Sends a brief HIGH signal to the Pico."""
    print(f"📡 Sending trigger signal from GPIO {TRIGGER_PIN}...")
    
    # Send a HIGH signal (3.3V)
    GPIO.output(TRIGGER_PIN, GPIO.HIGH)
    
    # Keep the signal high for a moment (e.g., 100ms)
    time.sleep(0.1)
    
    # Set the signal back to LOW
    GPIO.output(TRIGGER_PIN, GPIO.LOW)
    
    print("✅ Signal sent!")

try:
    print("🚀 Trigger script started. Sending signal in 5 seconds...")
    time.sleep(5)
    send_trigger()

except KeyboardInterrupt:
    print("\n⏹️ Program stopped by user.")

finally:
    # Clean up the GPIO pins on exit
    GPIO.cleanup()
    print("GPIO cleanup complete.")
