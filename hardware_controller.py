# In file: hardware_controller.py

import RPi.GPIO as GPIO
import time

class HardwareController:
    def __init__(self):
        # --- Pin Configuration (BCM numbering) ---
        self.STEP_PIN = 20
        self.DIR_PIN = 21
        self.ALM_PIN = 16
        self.HALL_PIN = 26
        self.INDUCTIVE_PIN = 19
        # --- ADDED: Legacy rotary limit switch pins (optional) ---
        self.HOME_SWITCH_PIN = 5  # Optional legacy home switch (not required if using hall)
        self.END_SWITCH_PIN = 6   # Optional second switch

        # --- ADDED: Slider motor limit switches ---
        # NOTE: Adjust these BCM pins to match wiring for the slider rail.
        self.SLIDER_MIN_PIN = 13
        self.SLIDER_MAX_PIN = 12

        # --- MODIFIED: Motor Configuration for MKS SERVO42C (NEMA 17) ---
        # A common setting for this driver is 16x microstepping on a 1.8° motor.
        # 200 full steps * 16 microsteps = 3200 pulses per revolution.
        # As always, verify this with your driver's DIP switch settings!
        self.PULSES_PER_REV = 3200
        self.SPEED_DELAY = 0.0005 # NEMA 17 may need a slightly slower speed

        # --- Setup GPIO ---
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.STEP_PIN, GPIO.OUT)
        GPIO.setup(self.DIR_PIN, GPIO.OUT)
        GPIO.setup(self.ALM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # --- ADDED: Setup limit switch pins ---
        GPIO.setup(self.HOME_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.END_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # --- ADDED: Setup slider switches ---
        GPIO.setup(self.SLIDER_MIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SLIDER_MAX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print("✅ Hardware Controller Initialized with Limit Switches")

    # --- MODIFIED: Homing Method (use hall sensor for home detection) ---
    def home_table(self):
        """Rotate the rotary motor until the hall sensor detects the magnet (home)."""
        print("Homing sequence (hall) started...")
        # Set direction for homing (e.g., counter-clockwise)
        GPIO.output(self.DIR_PIN, GPIO.LOW)

        # Rotate until hall is triggered (active low). Limit to ~1.5 revs to avoid loops
        max_steps = int(self.PULSES_PER_REV * 1.5)
        for _ in range(max_steps):
            if self.read_hall_sensor():
                # Optional: back off a bit and re-approach slowly for better accuracy
                print("✅ Hall detected. Homing complete.")
                return True

            GPIO.output(self.STEP_PIN, GPIO.HIGH)
            time.sleep(self.SPEED_DELAY)
            GPIO.output(self.STEP_PIN, GPIO.LOW)
            time.sleep(self.SPEED_DELAY)

        print("🛑 ERROR: Homing failed! Hall not detected within expected travel.")
        return False

    def move_degrees(self, degrees):
        """Move the rotary motor by the given degrees (signed). Positive=CW, Negative=CCW."""
        steps_to_move = int((abs(degrees) / 360.0) * self.PULSES_PER_REV)

        # Direction based on sign
        if degrees >= 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)

        print(f"Moving {steps_to_move} steps ({'CW' if degrees >= 0 else 'CCW'})...")
        for _ in range(steps_to_move):
            if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                print("🛑 ERROR: Motor Stalled!")
                return False

            GPIO.output(self.STEP_PIN, GPIO.HIGH)
            time.sleep(self.SPEED_DELAY)
            GPIO.output(self.STEP_PIN, GPIO.LOW)
            time.sleep(self.SPEED_DELAY)
        
        return True

    def read_hall_sensor(self):
        return GPIO.input(self.HALL_PIN) == GPIO.LOW

    def read_inductive_sensor(self):
        return GPIO.input(self.INDUCTIVE_PIN) == GPIO.LOW

    # --- ADDED: Slider limit switch reads ---
    def read_slider_min(self):
        return GPIO.input(self.SLIDER_MIN_PIN) == GPIO.LOW

    def read_slider_max(self):
        return GPIO.input(self.SLIDER_MAX_PIN) == GPIO.LOW

    def cleanup(self):
        GPIO.cleanup()
        print("GPIO cleanup complete.")