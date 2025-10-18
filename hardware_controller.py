# In file: hardware_controller.py

import RPi.GPIO as GPIO
import time

class HardwareController:
    def __init__(self):
        # --- Pin Configuration (BCM numbering) ---
        # Rotary Motor (OMC Closed-Loop Stepper)
        self.STEP_PIN = 20
        self.DIR_PIN = 21
        self.ENABLE_PIN = 22  # Enable pin for rotary motor
        self.ALM_PIN = 16
        
        # Sensors
        self.HALL_PIN = 26
        self.INDUCTIVE_PIN = 19
        
        # --- ADDED: Legacy rotary limit switch pins (optional) ---
        self.HOME_SWITCH_PIN = 5  # Optional legacy home switch (not required if using hall)
        self.END_SWITCH_PIN = 6   # Optional second switch

        # --- ADDED: Slider motor control pins ---
        self.SLIDER_STEP_PIN = 23
        self.SLIDER_DIR_PIN = 24
        self.SLIDER_ENABLE_PIN = 25  # Enable pin for slider motor
        
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
        
        # Rotary motor control pins
        GPIO.setup(self.STEP_PIN, GPIO.OUT)
        GPIO.setup(self.DIR_PIN, GPIO.OUT)
        GPIO.setup(self.ENABLE_PIN, GPIO.OUT)
        
        # Input pins (sensors and alarms)
        GPIO.setup(self.ALM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # --- ADDED: Setup limit switch pins ---
        GPIO.setup(self.HOME_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.END_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # --- ADDED: Setup slider switches ---
        GPIO.setup(self.SLIDER_MIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SLIDER_MAX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # --- ADDED: Setup slider motor control pins ---
        GPIO.setup(self.SLIDER_STEP_PIN, GPIO.OUT)
        GPIO.setup(self.SLIDER_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.SLIDER_ENABLE_PIN, GPIO.OUT)
        
        # Initialize enable pins (motors disabled by default)
        GPIO.output(self.ENABLE_PIN, GPIO.HIGH)  # HIGH = disabled for most drivers
        GPIO.output(self.SLIDER_ENABLE_PIN, GPIO.HIGH)  # HIGH = disabled for most drivers
        
        print("✅ Hardware Controller Initialized with Enable Pins and Limit Switches")

    # --- ADDED: Enable pin control methods ---
    def enable_rotary_motor(self, enabled=True):
        """Enable or disable the rotary motor."""
        # Most stepper drivers: LOW = enabled, HIGH = disabled
        # Some drivers are inverted, check your driver documentation
        GPIO.output(self.ENABLE_PIN, GPIO.LOW if enabled else GPIO.HIGH)
        status = "enabled" if enabled else "disabled"
        print(f"Rotary motor {status}")

    def enable_slider_motor(self, enabled=True):
        """Enable or disable the slider motor."""
        # Most stepper drivers: LOW = enabled, HIGH = disabled
        GPIO.output(self.SLIDER_ENABLE_PIN, GPIO.LOW if enabled else GPIO.HIGH)
        status = "enabled" if enabled else "disabled"
        print(f"Slider motor {status}")

    # --- MODIFIED: Homing Method (use hall sensor for home detection) ---
    def home_table(self):
        """Rotate the rotary motor until the hall sensor detects the magnet (home)."""
        print("Homing sequence (hall) started...")
        
        # Enable the motor before homing
        self.enable_rotary_motor(True)
        time.sleep(0.1)  # Allow motor to enable
        
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
        # Disable motor on failure
        self.enable_rotary_motor(False)
        return False

    def move_degrees(self, degrees, speed=50, accel_steps=100, decel_steps=100):
        """Move the rotary motor by the given degrees with acceleration/deceleration."""
        steps_to_move = int((abs(degrees) / 360.0) * self.PULSES_PER_REV)

        # Enable motor before movement
        self.enable_rotary_motor(True)
        time.sleep(0.1)  # Allow motor to enable

        # Direction based on sign
        if degrees >= 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)

        # Convert speed (0-100) to delay
        base_delay = self._speed_to_delay(speed)
        
        print(f"Moving {steps_to_move} steps ({'CW' if degrees >= 0 else 'CCW'}) at speed {speed}...")
        
        # Calculate acceleration/deceleration phases
        accel_phase = min(accel_steps, steps_to_move // 2)
        decel_phase = min(decel_steps, steps_to_move // 2)
        cruise_phase = steps_to_move - accel_phase - decel_phase
        
        try:
            # Acceleration phase
            for i in range(accel_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                
                # Gradually decrease delay (increase speed)
                delay = base_delay * (1.0 + (accel_phase - i) / accel_phase)
                self._step_motor(delay)
            
            # Cruise phase
            for _ in range(cruise_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                
                self._step_motor(base_delay)
            
            # Deceleration phase
            for i in range(decel_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                
                # Gradually increase delay (decrease speed)
                delay = base_delay * (1.0 + (i + 1) / decel_phase)
                self._step_motor(delay)
            
            return True
            
        except Exception as e:
            print(f"🛑 ERROR: Movement failed: {e}")
            return False
        finally:
            # Keep motor enabled for position holding (optional - can disable if desired)
            # self.enable_rotary_motor(False)
            pass
    
    def _speed_to_delay(self, speed):
        """Convert 0-100 speed to delay in seconds."""
        if speed <= 0:
            return 0.01  # Very slow if stopped
        # Convert to delay: 100 = 0.0005s, 1 = 0.01s (inverse relationship)
        return max(0.0005, 0.01 / (speed / 100.0))
    
    def _step_motor(self, delay):
        """Single step with given delay."""
        GPIO.output(self.STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.STEP_PIN, GPIO.LOW)
        time.sleep(delay)

    def read_hall_sensor(self):
        return GPIO.input(self.HALL_PIN) == GPIO.LOW

    def read_inductive_sensor(self):
        return GPIO.input(self.INDUCTIVE_PIN) == GPIO.LOW

    # --- ADDED: Slider limit switch reads ---
    def read_slider_min(self):
        return GPIO.input(self.SLIDER_MIN_PIN) == GPIO.LOW

    def read_slider_max(self):
        return GPIO.input(self.SLIDER_MAX_PIN) == GPIO.LOW

    # --- ADDED: Slider movement helpers ---
    def slider_move_to_max(self, speed_delay: float, max_pulses: int = 20000) -> bool:
        """Drive slider outward until MAX switch triggers or max_pulses reached."""
        # Enable slider motor
        self.enable_slider_motor(True)
        time.sleep(0.1)
        
        GPIO.output(self.SLIDER_DIR_PIN, GPIO.HIGH)
        for _ in range(max_pulses):
            if self.read_slider_max():
                return True
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
        return False

    def slider_move_to_min(self, speed_delay: float, max_pulses: int = 20000) -> bool:
        """Drive slider inward until MIN switch triggers or max_pulses reached."""
        # Enable slider motor
        self.enable_slider_motor(True)
        time.sleep(0.1)
        
        GPIO.output(self.SLIDER_DIR_PIN, GPIO.LOW)
        for _ in range(max_pulses):
            if self.read_slider_min():
                return True
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
        return False

    def cleanup(self):
        """Clean up GPIO and disable all motors."""
        print("Disabling all motors...")
        self.enable_rotary_motor(False)
        self.enable_slider_motor(False)
        GPIO.cleanup()
        print("GPIO cleanup complete.")