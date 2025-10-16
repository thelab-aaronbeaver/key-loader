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
        # --- ADDED: Limit Switch Pins ---
        self.HOME_SWITCH_PIN = 5  # The switch for the 0° position
        self.END_SWITCH_PIN = 6   # A second switch, if needed

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
        
        print("✅ Hardware Controller Initialized with Limit Switches")

    # --- ADDED: Homing Method ---
    def home_table(self):
        """Rotates the table until the home limit switch is triggered."""
        print("Homing sequence started...")
        # Set direction for homing (e.g., counter-clockwise)
        GPIO.output(self.DIR_PIN, GPIO.LOW)
        
        # Rotate until the switch is hit (pin goes LOW)
        # We'll rotate for a max of 1.1 revolutions to avoid infinite loops
        max_steps = int(self.PULSES_PER_REV * 1.1)
        for _ in range(max_steps):
            if GPIO.input(self.HOME_SWITCH_PIN) == GPIO.LOW:
                print("✅ Home switch triggered. Homing complete.")
                return True # Success
            
            # Pulse the motor one step
            GPIO.output(self.STEP_PIN, GPIO.HIGH)
            time.sleep(self.SPEED_DELAY)
            GPIO.output(self.STEP_PIN, GPIO.LOW)
            time.sleep(self.SPEED_DELAY)
            
        print("🛑 ERROR: Homing failed! Table rotated fully without hitting home switch.")
        return False # Failure

    def move_degrees(self, degrees):
        """Moves the motor a specified number of degrees and checks for errors."""
        steps_to_move = int((degrees / 360.0) * self.PULSES_PER_REV)
        
        # Set direction for normal cycle (e.g., clockwise)
        GPIO.output(self.DIR_PIN, GPIO.HIGH)
        
        print(f"Moving {steps_to_move} steps...")
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

    def cleanup(self):
        GPIO.cleanup()
        print("GPIO cleanup complete.")