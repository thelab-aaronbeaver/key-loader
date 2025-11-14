# In file: hardware_controller.py

import RPi.GPIO as GPIO
import time

class HardwareController:
    def __init__(self):
        # --- Pin Configuration (BCM numbering) ---
        # Rotary Motor (OMC Closed-Loop Stepper)
        self.STEP_PIN = 20
        self.DIR_PIN = 21
        self.ENABLE_PIN = 19  # Enable pin for rotary motor
        self.ALM_PIN = 16
        
        # Sensors
        self.HALL_PIN = 5
        self.INDUCTIVE_PIN = 22
        
        # --- ADDED: Legacy rotary limit switch pins (optional) ---
        self.HOME_SWITCH_PIN = 5  # Optional legacy home switch (not required if using hall)
        self.END_SWITCH_PIN = 6   # Optional second switch

        # --- ADDED: Slider motor control pins (MKS SERVO42C) ---
        self.SLIDER_STEP_PIN = 23
        self.SLIDER_DIR_PIN = 24
        self.SLIDER_ENABLE_PIN = 25  # Enable pin for slider motor (ENA)
        self.SLIDER_ALM_PIN = 18     # Alarm output from slider driver (ALM)
        
        # --- SERVO42C Configuration (12V Supply) ---
        # SERVO42C with 12V supply - balanced performance
        # Recommended: 4x microstepping (800 pulses/rev) for 12V operation
        self.SLIDER_PULSES_PER_REV = 400  # 4x microstepping (optimized for 12V)
        self.SLIDER_MAX_PULSE_RATE = 25000  # SERVO42C with 12V can handle 25kHz+
        
        # --- ADDED: Slider motor limit switches ---
        # NOTE: Adjust these BCM pins to match wiring for the slider rail.
        self.SLIDER_MIN_PIN = 27
        self.SLIDER_MAX_PIN = 17

        # --- ADDED: Key catcher motor control pins (MKS SERVO42C #2) ---
        self.KEY_CATCHER_STEP_PIN = 12
        self.KEY_CATCHER_DIR_PIN = 13
        self.KEY_CATCHER_ENABLE_PIN = 6

        # --- Key Catcher Configuration (12V Supply) ---
        # SERVO42C with 12V supply - same as slider motor
        self.KEY_CATCHER_PULSES_PER_REV = 800  # 4x microstepping (optimized for 12V)
        self.KEY_CATCHER_MAX_PULSE_RATE = 25000  # SERVO42C with 12V can handle 25kHz+
        
        # Key catcher position tracking
        self.key_catcher_current_position = 0  # Current position in steps
        self.key_catcher_keys_processed = 0     # Keys processed since last reset

        # --- MODIFIED: Motor Configuration for CL57T Driver (Rotary) ---
        # CL57T is configured for 3200 pulses per revolution (16x microstepping on 1.8° motor).
        # 200 full steps * 16 microsteps = 3200 pulses per revolution.
        # This matches the CL57T DIP switch settings for 16x microstepping.
        self.PULSES_PER_REV = 3200
        self.SPEED_DELAY = 0.0002 # CL57T can handle faster speeds than basic drivers

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
        GPIO.setup(self.SLIDER_ALM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # --- ADDED: Setup key catcher motor control pins ---
        GPIO.setup(self.KEY_CATCHER_STEP_PIN, GPIO.OUT)
        GPIO.setup(self.KEY_CATCHER_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.KEY_CATCHER_ENABLE_PIN, GPIO.OUT)
        
        # Initialize enable pins (motors disabled by default)
        GPIO.output(self.ENABLE_PIN, GPIO.HIGH)  # HIGH = disabled for most drivers
        GPIO.output(self.SLIDER_ENABLE_PIN, GPIO.HIGH)  # HIGH = disabled for most drivers
        GPIO.output(self.KEY_CATCHER_ENABLE_PIN, GPIO.HIGH)  # HIGH = disabled for most drivers
        
        print("✅ Hardware Controller Initialized with Enable Pins, Limit Switches, Slider Alarm, and Key Catcher Motor")

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

    def read_slider_alarm(self):
        """Return True if the slider driver reports a fault/stall (ALM active)."""
        # Most drivers expose ALM as active-low (LOW = fault). Adjust if needed.
        return GPIO.input(self.SLIDER_ALM_PIN) == GPIO.LOW

    def enable_key_catcher_motor(self, enabled=True):
        """Enable or disable the key catcher motor."""
        # Most stepper drivers: LOW = enabled, HIGH = disabled
        GPIO.output(self.KEY_CATCHER_ENABLE_PIN, GPIO.LOW if enabled else GPIO.HIGH)
        status = "enabled" if enabled else "disabled"
        print(f"Key catcher motor {status}")

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
        """Convert 0-100 speed to delay in seconds for rotary motor (300 RPM maximum)."""
        if speed <= 0:
            return 0.01  # Very slow if stopped
        # Convert to delay: 100 = 0.0000625s (0.0625ms) = 300 RPM, 1 = 0.00625s (inverse relationship)
        # Optimized for CL57T driver - 300 RPM maximum
        return max(0.00000625, 0.000625 / (speed / 100.0))
    
    def _servo42c_speed_to_delay(self, speed):
        """Convert 0-100 speed to delay for SERVO42C (750 RPM maximum)."""
        if speed <= 0:
           return 0.0001  # Very slow if stopped
        # SERVO42C optimized for 750 RPM maximum
        # 100 = 0.0001s (0.1ms) = 750 RPM, 50 = 0.0002s (0.2ms) = 375 RPM
        return max(0.00001, 0.001 / (speed / 100.0))
    
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

    # --- ADDED: Debounced limit switch reads to prevent phantom triggers ---
    def read_slider_min_debounced(self):
        """Read MIN switch with debouncing to prevent phantom triggers."""
        readings = []
        for _ in range(5):  # Take 5 readings
            readings.append(GPIO.input(self.SLIDER_MIN_PIN) == GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
        
        # Return True only if majority of readings are True
        return sum(readings) >= 3

    def read_slider_max_debounced(self):
        """Read MAX switch with debouncing to prevent phantom triggers."""
        readings = []
        for _ in range(5):  # Take 5 readings
            readings.append(GPIO.input(self.SLIDER_MAX_PIN) == GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
        
        # Return True only if majority of readings are True
        return sum(readings) >= 3

    # --- ADDED: Slider movement helpers ---
    def slider_move_to_max(self, speed: int, max_pulses: int = 20000, accel_steps: int = 50, decel_steps: int = 50, ultra_fast: bool = False) -> bool:
        """Drive slider outward until MAX switch triggers or max_pulses reached with acceleration/deceleration."""
        # Enable slider motor
        self.enable_slider_motor(True)
        if not ultra_fast:
            time.sleep(0.1)  # Skip delay in ultra-fast mode
        
        # Convert speed to SERVO42C-optimized delay
        speed_delay = self._servo42c_speed_to_delay(speed)
        
        GPIO.output(self.SLIDER_DIR_PIN, GPIO.HIGH)
        print(f"Moving slider to MAX: speed={speed}, delay={speed_delay:.6f}s, max_pulses={max_pulses}, accel={accel_steps}, decel={decel_steps}, ultra_fast={ultra_fast}")
        
        if ultra_fast:
            # ULTRA-FAST MODE: Minimal acceleration, maximum speed for SERVO42C (12V)
            accel_phase = min(8, max_pulses // 80)  # 8 steps acceleration for SERVO42C 12V
            decel_phase = min(8, max_pulses // 80)  # 8 steps deceleration for SERVO42C 12V
        else:
            # OPTIMIZED for SERVO42C (800 pulses/rev with 4x microstepping, 12V)
            accel_phase = min(accel_steps, max_pulses // 15)  # Use 1/15 for SERVO42C 12V
            decel_phase = min(decel_steps, max_pulses // 15)  # Use 1/15 for SERVO42C 12V
        
        cruise_phase = max(0, max_pulses - accel_phase - decel_phase)  # Ensure non-negative
        
        print(f"Slider MAX phases: accel={accel_phase}, cruise={cruise_phase}, decel={decel_phase}")
        
        step_count = 0
        
        # Acceleration phase (short for SERVO42C)
        for i in range(accel_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during accel phase")
                return False
            if self.read_slider_max_debounced():
                print(f"MAX switch triggered at step {step_count} (accel phase)")
                return True
            # Gradually decrease delay (increase speed)
            delay = speed_delay * (1.0 + (accel_phase - i) / accel_phase)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Cruise phase
        for _ in range(cruise_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during cruise phase")
                return False
            if ultra_fast:
                # ULTRA-FAST: Use non-debounced reading for maximum speed
                if self.read_slider_max():
                    print(f"MAX switch triggered at step {step_count} (cruise phase - ultra-fast)")
                    return True
            else:
                if self.read_slider_max_debounced():
                    print(f"MAX switch triggered at step {step_count} (cruise phase)")
                    return True
            
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
            step_count += 1
        
        # Deceleration phase (short for SERVO42C)
        for i in range(decel_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during decel phase")
                return False
            if self.read_slider_max_debounced():
                print(f"MAX switch triggered at step {step_count} (decel phase)")
                return True
            # Gradually increase delay (decrease speed)
            delay = speed_delay * (1.0 + (i + 1) / decel_phase)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        print(f"MAX movement completed: {step_count} steps, MAX switch not triggered")
        return False

    def slider_move_to_min(self, speed: int, max_pulses: int = 20000, accel_steps: int = 50, decel_steps: int = 50, ultra_fast: bool = False) -> bool:
        """Drive slider inward until MIN switch triggers or max_pulses reached with acceleration/deceleration."""
        # Enable slider motor
        self.enable_slider_motor(True)
        if not ultra_fast:
            time.sleep(0.1)  # Skip delay in ultra-fast mode
        
        # Convert speed to SERVO42C-optimized delay
        speed_delay = self._servo42c_speed_to_delay(speed)
        
        GPIO.output(self.SLIDER_DIR_PIN, GPIO.LOW)
        print(f"Moving slider to MIN: speed={speed}, delay={speed_delay:.6f}s, max_pulses={max_pulses}, accel={accel_steps}, decel={decel_steps}, ultra_fast={ultra_fast}")
        
        if ultra_fast:
            # ULTRA-FAST MODE: Minimal acceleration, maximum speed for SERVO42C (12V)
            accel_phase = min(8, max_pulses // 80)  # 8 steps acceleration for SERVO42C 12V
            decel_phase = min(8, max_pulses // 80)  # 8 steps deceleration for SERVO42C 12V
        else:
            # OPTIMIZED for SERVO42C (800 pulses/rev with 4x microstepping, 12V)
            accel_phase = min(accel_steps, max_pulses // 15)  # Use 1/15 for SERVO42C 12V
            decel_phase = min(decel_steps, max_pulses // 15)  # Use 1/15 for SERVO42C 12V
        
        cruise_phase = max(0, max_pulses - accel_phase - decel_phase)  # Ensure non-negative
        
        print(f"Slider MIN phases: accel={accel_phase}, cruise={cruise_phase}, decel={decel_phase}")
        
        step_count = 0
        
        # Acceleration phase (short for SERVO42C)
        for i in range(accel_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during accel phase")
                return False
            if self.read_slider_min_debounced():
                print(f"MIN switch triggered at step {step_count} (accel phase)")
                return True
            # Gradually decrease delay (increase speed)
            delay = speed_delay * (1.0 + (accel_phase - i) / accel_phase)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Cruise phase
        for _ in range(cruise_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during cruise phase")
                return False
            if ultra_fast:
                # ULTRA-FAST: Use non-debounced reading for maximum speed
                if self.read_slider_min():
                    print(f"MIN switch triggered at step {step_count} (cruise phase - ultra-fast)")
                    return True
            else:
                if self.read_slider_min_debounced():
                    print(f"MIN switch triggered at step {step_count} (cruise phase)")
                    return True
            
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
            step_count += 1
        
        # Deceleration phase (short for SERVO42C)
        for i in range(decel_phase):
            if self.read_slider_alarm():
                print("🛑 ERROR: Slider driver alarm during decel phase")
                return False
            if self.read_slider_min_debounced():
                print(f"MIN switch triggered at step {step_count} (decel phase)")
                return True
            # Gradually increase delay (decrease speed)
            delay = speed_delay * (1.0 + (i + 1) / decel_phase)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        print(f"MIN movement completed: {step_count} steps, MIN switch not triggered")
        return False

    # --- ADDED: Key catcher motor control methods ---
    def key_catcher_move_steps(self, steps, speed=80, direction=1):
        """
        Move the key catcher motor a specific number of steps.
        
        Args:
            steps: Number of steps to move
            speed: Speed (0-100)
            direction: 1 for forward, -1 for reverse (or use negative steps)
        
        Returns:
            bool: True if movement successful
        """
        if steps == 0:
            return True
        
        # Handle negative steps
        if steps < 0:
            steps = abs(steps)
            direction = -direction
        
        # Enable motor
        self.enable_key_catcher_motor(True)
        time.sleep(0.05)  # Brief enable delay
        
        # Set direction
        GPIO.output(self.KEY_CATCHER_DIR_PIN, GPIO.HIGH if direction > 0 else GPIO.LOW)
        
        # Convert speed to delay using SERVO42C speed calculation
        speed_delay = self._servo42c_speed_to_delay(speed)
        
        print(f"Key catcher moving {steps} steps ({'forward' if direction > 0 else 'reverse'}) at speed {speed}")
        
        # Perform movement with simple acceleration/deceleration
        accel_steps = min(20, steps // 4)  # Short acceleration for key catcher
        decel_steps = min(20, steps // 4)
        cruise_steps = max(0, steps - accel_steps - decel_steps)
        
        step_count = 0
        
        # Acceleration phase
        for i in range(accel_steps):
            delay = speed_delay * (1.0 + (accel_steps - i) / accel_steps)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Cruise phase
        for _ in range(cruise_steps):
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
            step_count += 1
        
        # Deceleration phase
        for i in range(decel_steps):
            delay = speed_delay * (1.0 + (i + 1) / decel_steps)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Update position tracking
        self.key_catcher_current_position += (steps * direction)
        
        print(f"Key catcher moved {step_count} steps. Current position: {self.key_catcher_current_position}")
        return True
    
    def key_catcher_move_to_position(self, target_position, speed=80):
        """
        Move key catcher to an absolute position.
        
        Args:
            target_position: Target position in steps
            speed: Speed (0-100)
        
        Returns:
            bool: True if movement successful
        """
        steps_to_move = target_position - self.key_catcher_current_position
        if steps_to_move == 0:
            print(f"Key catcher already at position {target_position}")
            return True
        
        return self.key_catcher_move_steps(steps_to_move, speed)
    
    def key_catcher_reset_position(self, speed=80):
        """
        Reset key catcher to home position (0 steps).
        
        Args:
            speed: Speed (0-100)
        
        Returns:
            bool: True if movement successful
        """
        print(f"Resetting key catcher from position {self.key_catcher_current_position} to 0")
        return self.key_catcher_move_to_position(0, speed)
    
    def key_catcher_set_position(self, position):
        """Set the current position without moving (for calibration)."""
        self.key_catcher_current_position = position
        print(f"Key catcher position set to {position}")
    
    def key_catcher_get_position(self):
        """Get the current position of the key catcher."""
        return self.key_catcher_current_position
    
    def key_catcher_increment_key_count(self):
        """Increment the key counter."""
        self.key_catcher_keys_processed += 1
        return self.key_catcher_keys_processed
    
    def key_catcher_reset_key_count(self):
        """Reset the key counter."""
        self.key_catcher_keys_processed = 0
        print("Key catcher key count reset to 0")

    def cleanup(self):
        """Clean up GPIO and disable all motors."""
        print("Disabling all motors...")
        self.enable_rotary_motor(False)
        self.enable_slider_motor(False)
        self.enable_key_catcher_motor(False)
        GPIO.cleanup()

        print("GPIO cleanup complete.")









