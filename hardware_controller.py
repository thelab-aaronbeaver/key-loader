# In file: hardware_controller.py

import RPi.GPIO as GPIO
import time

class HardwareController:
    def __init__(self):
        # --- Pin Configuration (BCM numbering) ---
        # Rotary Motor (OMC Closed-Loop Stepper)
        self.STEP_PIN = 20
        self.DIR_PIN = 21
        self.ENABLE_PIN = 12  # Enable pin for rotary motor
        self.ALM_PIN = 16
        
        # Sensors
        self.HALL_PIN = 27
        self.INDUCTIVE_PIN = 5
    
        
        # --- ADDED: Legacy rotary limit switch pins (optional) ---
        self.HOME_SWITCH_PIN = 7  # Optional legacy home switch (not required if using hall)
        self.END_SWITCH_PIN = 8   # Optional second switch

        # --- ADDED: Slider motor control pins (MKS SERVO42C) ---
        self.SLIDER_STEP_PIN = 23
        self.SLIDER_DIR_PIN = 24
        self.SLIDER_ENABLE_PIN = 25  # Enable pin for slider motor (ENA)
        
        # --- SERVO42C Configuration (12V Supply) ---
        # SERVO42C with 12V supply - balanced performance
        # Recommended: 4x microstepping (800 pulses/rev) for 12V operation
        self.SLIDER_PULSES_PER_REV = 800  # 4x microstepping (optimized for 12V)
        self.SLIDER_MAX_PULSE_RATE = 25000  # SERVO42C with 12V can handle 25kHz+
        
        # --- ADDED: Slider motor limit switches ---
        # NOTE: Adjust these BCM pins to match wiring for the slider rail.
        self.SLIDER_MIN_PIN = 4  # Slider MIN limit switch
        self.SLIDER_MAX_PIN = 17  # Slider MAX limit switch

        # --- ADDED: Key catcher motor control pins (MKS SERVO42C #2) ---
        self.KEY_CATCHER_STEP_PIN = 26
        self.KEY_CATCHER_DIR_PIN = 19
        self.KEY_CATCHER_ENABLE_PIN = 13
        
        # --- ADDED: Key catcher limit switches ---
        self.KEY_CATCHER_HOME_PIN = 18   # Home position limit switch
        self.KEY_CATCHER_MAX_PIN = 6    # Max/pause/stop position limit switch

        # --- Key Catcher Configuration (12V Supply) ---
        # SERVO42C with 12V supply - same as slider motor
        self.KEY_CATCHER_PULSES_PER_REV = 800  # 4x microstepping (optimized for 12V)
        self.KEY_CATCHER_MAX_PULSE_RATE = 25000  # SERVO42C with 12V can handle 25kHz+
        
        # Key catcher position tracking
        self.key_catcher_current_position = 0  # Current position in steps
        self.key_catcher_keys_processed = 0     # Keys processed since last reset

        # Rotary position tracking (steps from calibrated step 0 / Set Home reference)
        self.rotary_current_steps = 0

        # --- MODIFIED: Motor Configuration for CL57T Driver (Rotary) ---
        # CL57T is configured for 3200 pulses per revolution (16x microstepping on 1.8° motor).
        # 200 full steps * 16 microsteps = 3200 pulses per revolution.
        # This matches the CL57T DIP switch settings for 16x microstepping.
        self.PULSES_PER_REV = 3200
        self.SPEED_DELAY = 0.0002 # CL57T can handle faster speeds than basic drivers
        # Give driver time to latch DIR before first STEP pulse.
        self.DIR_SETUP_DELAY = 0.002

        # --- Setup GPIO ---
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Rotary motor control pins
        GPIO.setup(self.STEP_PIN, GPIO.OUT)
        GPIO.setup(self.DIR_PIN, GPIO.OUT)
        GPIO.setup(self.ENABLE_PIN, GPIO.OUT)
        
        # Input pins (sensors and alarms)
        GPIO.setup(self.ALM_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Hall sensor with voltage divider (22kΩ + 3.3kΩ)
        # Current readings: 1.2V (inactive) / 0.02V (active)
        # 1.2V is borderline - using pull-down to help distinguish
        GPIO.setup(self.HALL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # Inductive sensor with voltage divider (22kΩ + 3.3kΩ)
        # Current readings: 1.2V (inactive) / 0.02V (active)
        # 1.2V is borderline - using pull-down to help distinguish
        GPIO.setup(self.INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
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
        
        # --- ADDED: Setup key catcher motor control pins ---
        GPIO.setup(self.KEY_CATCHER_STEP_PIN, GPIO.OUT)
        GPIO.setup(self.KEY_CATCHER_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.KEY_CATCHER_ENABLE_PIN, GPIO.OUT)
        
        # --- ADDED: Setup key catcher limit switches ---
        GPIO.setup(self.KEY_CATCHER_HOME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.KEY_CATCHER_MAX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
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
        time.sleep(self.DIR_SETUP_DELAY)

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

    def degrees_to_steps(self, degrees):
        """Convert degrees to integer motor pulses (always positive)."""
        return int((abs(degrees) / 360.0) * self.PULSES_PER_REV)

    def reset_rotary_step_counter(self):
        """Reset rotary step position to calibrated step 0."""
        self.rotary_current_steps = 0
        print("Rotary step counter reset to 0")

    def shortest_step_delta_to_zero(self, current_steps=None):
        """
        Signed step count for the shortest path back to step 0.
        Uses modulo one revolution (e.g. 16640 net steps -> move -640, not -16640).
        """
        if current_steps is None:
            current_steps = self.rotary_current_steps
        if current_steps == 0:
            return 0
        rev = self.PULSES_PER_REV
        pos = current_steps % rev
        if pos > rev // 2:
            pos -= rev
        return -pos

    def steps_to_degrees(self, steps):
        """Convert signed step count to degrees (for logging/display)."""
        return (float(steps) / self.PULSES_PER_REV) * 360.0

    def move_steps(self, steps, speed=50, accel_steps=100, decel_steps=100):
        """Move the rotary motor by an exact signed step count."""
        if steps == 0:
            return True

        steps_to_move = abs(int(steps))
        direction_sign = 1 if steps >= 0 else -1

        self.enable_rotary_motor(True)
        time.sleep(0.1)

        if direction_sign >= 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)
        time.sleep(self.DIR_SETUP_DELAY)
        dir_read = int(GPIO.input(self.DIR_PIN))
        print(f"DIR set to {'HIGH' if dir_read else 'LOW'} for {'CW' if direction_sign >= 0 else 'CCW'}")

        base_delay = self._speed_to_delay(speed)
        print(f"Moving {steps_to_move} steps ({'CW' if direction_sign >= 0 else 'CCW'}) at speed {speed}...")

        accel_phase = min(accel_steps, steps_to_move // 2)
        decel_phase = min(decel_steps, steps_to_move // 2)
        cruise_phase = steps_to_move - accel_phase - decel_phase

        try:
            for i in range(accel_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                delay = base_delay * (1.0 + (accel_phase - i) / accel_phase)
                self._step_motor(delay)

            for _ in range(cruise_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                self._step_motor(base_delay)

            for i in range(decel_phase):
                if GPIO.input(self.ALM_PIN) == GPIO.LOW:
                    print("🛑 ERROR: Motor Stalled!")
                    return False
                delay = base_delay * (1.0 + (i + 1) / decel_phase)
                self._step_motor(delay)

            self.rotary_current_steps += direction_sign * steps_to_move
            return True

        except Exception as e:
            print(f"🛑 ERROR: Movement failed: {e}")
            return False

    def move_degrees(self, degrees, speed=50, accel_steps=100, decel_steps=100):
        """Move the rotary motor by the given degrees with acceleration/deceleration."""
        steps_to_move = self.degrees_to_steps(degrees)
        direction_sign = 1 if degrees >= 0 else -1

        # Enable motor before movement
        self.enable_rotary_motor(True)
        time.sleep(0.1)  # Allow motor to enable

        # Direction based on sign
        if degrees >= 0:
            GPIO.output(self.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.DIR_PIN, GPIO.LOW)
        time.sleep(self.DIR_SETUP_DELAY)
        dir_read = int(GPIO.input(self.DIR_PIN))
        print(f"DIR set to {'HIGH' if dir_read else 'LOW'} for {'CW' if degrees >= 0 else 'CCW'}")

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
            
            self.rotary_current_steps += direction_sign * steps_to_move
            return True
            
        except Exception as e:
            print(f"🛑 ERROR: Movement failed: {e}")
            return False
        finally:
            # Keep motor enabled for position holding (optional - can disable if desired)
            # self.enable_rotary_motor(False)
            pass

    def rotary_dir_test(self, cycles=4, settle_ms=5, hold_ms=250):
        """
        Toggle rotary DIR pin and report readback timing.

        Args:
            cycles: Number of toggles to perform
            settle_ms: Wait time after each DIR write before settled readback
            hold_ms: Additional hold time per state for probing with a meter/scope

        Returns:
            dict: Direction toggle/readback timing details
        """
        cycles = max(1, int(cycles))
        settle_s = max(0.0, float(settle_ms) / 1000.0)
        hold_s = max(0.0, float(hold_ms) / 1000.0)

        # Ensure output is actively driven during test.
        self.enable_rotary_motor(True)
        time.sleep(0.05)

        initial_read = int(GPIO.input(self.DIR_PIN))
        target_state = GPIO.LOW if initial_read == GPIO.HIGH else GPIO.HIGH
        transitions = []

        for idx in range(cycles):
            t0 = time.perf_counter()
            GPIO.output(self.DIR_PIN, target_state)
            t1 = time.perf_counter()
            immediate_read = int(GPIO.input(self.DIR_PIN))
            time.sleep(settle_s)
            t2 = time.perf_counter()
            settled_read = int(GPIO.input(self.DIR_PIN))
            if hold_s > 0:
                time.sleep(hold_s)
            t3 = time.perf_counter()

            transitions.append({
                "index": idx + 1,
                "target": "HIGH" if target_state == GPIO.HIGH else "LOW",
                "target_value": int(target_state),
                "read_immediate": immediate_read,
                "read_settled": settled_read,
                "write_overhead_ms": (t1 - t0) * 1000.0,
                "settle_wait_ms": (t2 - t1) * 1000.0,
                "hold_wait_ms": (t3 - t2) * 1000.0
            })

            target_state = GPIO.LOW if target_state == GPIO.HIGH else GPIO.HIGH

        return {
            "success": True,
            "pin": self.DIR_PIN,
            "initial_read": initial_read,
            "cycles": cycles,
            "settle_ms_requested": float(settle_ms),
            "hold_ms_requested": float(hold_ms),
            "transitions": transitions
        }
    
    def _speed_to_delay(self, speed):
        """Convert 0-100 speed to delay in seconds for rotary motor (300 RPM maximum)."""
        if speed <= 0:
            return 0.01  # Very slow if stopped
        # Convert to delay: 100 = 0.0000625s (0.0625ms) = 300 RPM, 1 = 0.00625s (inverse relationship)
        # Optimized for CL57T driver - 300 RPM maximum
        return max(0.00000625, 0.000625 / (speed / 100.0))
    
    def _servo42c_speed_to_delay(self, speed, max_pulse_rate, min_delay=0.00004):
        """Convert 0-100 speed to half-period delay using configured max pulse rate."""
        if speed <= 0:
           return 0.01  # Very slow if stopped
        pulse_rate = max_pulse_rate * (speed / 100.0)  # pulses per second
        # Keep a practical floor for Python timing + motor torque at startup.
        return max(min_delay, 1.0 / (2.0 * pulse_rate))
    
    def _step_motor(self, delay):
        """Single step with given delay."""
        GPIO.output(self.STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.STEP_PIN, GPIO.LOW)
        time.sleep(delay)

    def read_hall_sensor(self):
        """Read Hall sensor through voltage divider.
        
        Current setup: 22kΩ + 3.3kΩ voltage divider
        Voltages: 1.2V (inactive) / 0.02V (active)
        
        ⚠️ 1.2V is at GPIO threshold - may be unreliable!
        For better reliability, use 22kΩ + 10kΩ to get ~2V inactive.
        """
        return GPIO.input(self.HALL_PIN) == GPIO.LOW

    def read_inductive_sensor(self):
        """Read inductive sensor through voltage divider.
        
        Current setup: 22kΩ + 3.3kΩ voltage divider
        Voltages: 1.2V (inactive) / 0.02V (active)
        
        NPN NO sensor behavior:
        - No metal (inactive): Sensor output = OPEN CIRCUIT → Pull-up brings to 3.3V (HIGH)
        - Metal detected (active): Sensor output = GND → Pin reads 0V (LOW)
        
        Current external voltages without pull-up: 0.3V (idle) / 0.025V (active)
        Both read as LOW, can't distinguish! Internal pull-up fixes this.
        
        With internal pull-up:
        - No metal: Pin pulled HIGH to 3.3V
        - Metal detected: Sensor pulls to GND (LOW)
        
        ⚠️ NOTE: For better reliability, add external 10kΩ pull-up to +12V
           See inductive_sensor_fix.md for proper wiring
        """
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

    # --- ADDED: Key catcher limit switch reads ---
    def read_key_catcher_home(self):
        """Read key catcher HOME limit switch (non-debounced)."""
        return GPIO.input(self.KEY_CATCHER_HOME_PIN) == GPIO.LOW

    def read_key_catcher_max(self):
        """Read key catcher MAX limit switch (non-debounced)."""
        return GPIO.input(self.KEY_CATCHER_MAX_PIN) == GPIO.LOW

    def read_key_catcher_home_debounced(self):
        """Read key catcher HOME switch with debouncing to prevent phantom triggers."""
        readings = []
        for _ in range(5):  # Take 5 readings
            readings.append(GPIO.input(self.KEY_CATCHER_HOME_PIN) == GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
        
        # Return True only if majority of readings are True
        return sum(readings) >= 3

    def read_key_catcher_max_debounced(self):
        """Read key catcher MAX switch with debouncing to prevent phantom triggers."""
        readings = []
        for _ in range(5):  # Take 5 readings
            readings.append(GPIO.input(self.KEY_CATCHER_MAX_PIN) == GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
        
        # Return True only if majority of readings are True
        return sum(readings) >= 3

    # --- ADDED: Slider movement helpers ---
    def slider_move_to_max(self, speed: int, max_pulses: int = 20000, accel_steps: int = 50, decel_steps: int = 50, ultra_fast: bool = False, max_seconds=None) -> bool:
        """Drive slider outward until MAX switch triggers or safety limits are reached."""
        # Enable slider motor
        self.enable_slider_motor(True)
        if not ultra_fast:
            time.sleep(0.1)  # Skip delay in ultra-fast mode
        
        # Convert speed to SERVO42C-optimized delay
        speed_delay = self._servo42c_speed_to_delay(speed, self.SLIDER_MAX_PULSE_RATE)
        
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
        start_time = time.time()
        
        # Acceleration phase (short for SERVO42C)
        ramp_start_multiplier = 4.0 if speed_delay <= 0.00005 else 2.0
        for i in range(accel_phase):
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MAX): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
                return False
            if self.read_slider_max_debounced():
                print(f"MAX switch triggered at step {step_count} (accel phase)")
                return True
            # Gradually decrease delay (increase speed)
            progress = (accel_phase - i) / accel_phase
            delay = speed_delay * (1.0 + (ramp_start_multiplier - 1.0) * progress)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Cruise phase
        for _ in range(cruise_phase):
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MAX): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
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
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MAX): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
                return False
            if self.read_slider_max_debounced():
                print(f"MAX switch triggered at step {step_count} (decel phase)")
                return True
            # Gradually increase delay (decrease speed)
            progress = (i + 1) / decel_phase
            delay = speed_delay * (1.0 + (ramp_start_multiplier - 1.0) * progress)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        print(f"🛑 SLIDER SAFETY TRIP (MAX): switch not triggered within {step_count} steps")
        self.enable_slider_motor(False)
        return False

    def slider_move_to_min(self, speed: int, max_pulses: int = 20000, accel_steps: int = 50, decel_steps: int = 50, ultra_fast: bool = False, max_seconds=None) -> bool:
        """Drive slider inward until MIN switch triggers or safety limits are reached."""
        # Enable slider motor
        self.enable_slider_motor(True)
        if not ultra_fast:
            time.sleep(0.1)  # Skip delay in ultra-fast mode
        
        # Convert speed to SERVO42C-optimized delay
        speed_delay = self._servo42c_speed_to_delay(speed, self.SLIDER_MAX_PULSE_RATE)
        
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
        start_time = time.time()
        
        # Acceleration phase (short for SERVO42C)
        ramp_start_multiplier = 4.0 if speed_delay <= 0.00005 else 2.0
        for i in range(accel_phase):
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MIN): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
                return False
            if self.read_slider_min_debounced():
                print(f"MIN switch triggered at step {step_count} (accel phase)")
                return True
            # Gradually decrease delay (increase speed)
            progress = (accel_phase - i) / accel_phase
            delay = speed_delay * (1.0 + (ramp_start_multiplier - 1.0) * progress)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        # Cruise phase
        for _ in range(cruise_phase):
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MIN): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
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
            if max_seconds is not None and (time.time() - start_time) >= max_seconds:
                print(f"🛑 SLIDER SAFETY TRIP (MIN): movement timeout after {max_seconds:.2f}s at step {step_count}")
                self.enable_slider_motor(False)
                return False
            if self.read_slider_min_debounced():
                print(f"MIN switch triggered at step {step_count} (decel phase)")
                return True
            # Gradually increase delay (decrease speed)
            progress = (i + 1) / decel_phase
            delay = speed_delay * (1.0 + (ramp_start_multiplier - 1.0) * progress)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.SLIDER_STEP_PIN, GPIO.LOW)
            time.sleep(delay)
            step_count += 1
        
        print(f"🛑 SLIDER SAFETY TRIP (MIN): switch not triggered within {step_count} steps")
        self.enable_slider_motor(False)
        return False

    # --- ADDED: Key catcher motor control methods ---
    def key_catcher_home(self, speed=50, max_steps=5000):
        """
        Home the key catcher by moving towards the HOME limit switch.
        
        Args:
            speed: Speed (0-100)
            max_steps: Maximum steps to travel before giving up
        
        Returns:
            bool: True if homing successful, False otherwise
        """
        print("Key catcher homing sequence started...")
        
        # Enable motor
        self.enable_key_catcher_motor(True)
        time.sleep(0.1)  # Allow motor to enable
        
        # Move towards home (reverse direction)
        GPIO.output(self.KEY_CATCHER_DIR_PIN, GPIO.LOW)
        
        # Convert speed to delay
        speed_delay = self._servo42c_speed_to_delay(speed, self.KEY_CATCHER_MAX_PULSE_RATE)
        
        # Move until HOME switch is triggered or max steps reached
        for step in range(max_steps):
            if self.read_key_catcher_home_debounced():
                print(f"✅ Key catcher HOME switch triggered at step {step}")
                # Reset position to 0 since we're at home
                self.key_catcher_current_position = 0
                return True
            
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
        
        print(f"🛑 ERROR: Key catcher homing failed! HOME switch not triggered within {max_steps} steps")
        return False
    
    def key_catcher_move_steps(self, steps, speed=80, direction=1, check_limits=True):
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
        speed_delay = self._servo42c_speed_to_delay(speed, self.KEY_CATCHER_MAX_PULSE_RATE)
        
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
    
    def key_catcher_test_cycle(self, speed=80):
        """
        Test the key catcher by moving from home to pause/stop position and back.
        
        This function:
        1. Homes to the HOME limit switch (pin 6)
        2. Moves forward until the MAX/PAUSE limit switch is triggered (pin 5)
        3. Returns back to HOME position
        
        Args:
            speed: Speed (0-100) for movements
        
        Returns:
            dict: Test results with success status and messages
        """
        results = {
            "success": False,
            "home_success": False,
            "max_success": False,
            "return_success": False,
            "messages": []
        }
        
        print(f"\n{'='*80}")
        print(f"🔧 KEY CATCHER TEST CYCLE STARTED")
        print(f"{'='*80}\n")
        
        # Step 1: Home to HOME limit switch (pin 6)
        print("Step 1: Homing to HOME limit switch (pin 6)...")
        results["messages"].append("Homing to HOME limit switch...")
        
        home_success = self.key_catcher_home(speed=speed, max_steps=8000)
        results["home_success"] = home_success
        
        if not home_success:
            results["messages"].append("❌ FAILED: Could not reach HOME limit switch")
            print(f"\n{'='*80}")
            print(f"❌ TEST FAILED: Could not reach HOME limit switch")
            print(f"{'='*80}\n")
            return results
        
        results["messages"].append("✅ HOME limit switch reached")
        print("✅ HOME limit switch reached at pin 6")
        time.sleep(0.5)  # Brief pause at home
        
        # Step 2: Move forward until MAX/PAUSE limit switch is triggered (pin 5)
        print("\nStep 2: Moving to PAUSE/STOP limit switch (pin 5)...")
        results["messages"].append("Moving to PAUSE/STOP limit switch...")
        
        # Enable motor
        self.enable_key_catcher_motor(True)
        time.sleep(0.1)
        
        # Set direction forward
        GPIO.output(self.KEY_CATCHER_DIR_PIN, GPIO.HIGH)
        
        # Convert speed to delay
        speed_delay = self._servo42c_speed_to_delay(speed, self.KEY_CATCHER_MAX_PULSE_RATE)
        
        # Move until MAX switch is triggered
        max_steps = 8000  # Safety limit
        steps_traveled = 0
        max_triggered = False
        
        for step in range(max_steps):
            if self.read_key_catcher_max_debounced():
                print(f"✅ PAUSE/STOP limit switch triggered at step {step}")
                results["messages"].append(f"✅ PAUSE/STOP limit switch reached after {step} steps")
                max_triggered = True
                steps_traveled = step
                break
            
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
        
        results["max_success"] = max_triggered
        
        if not max_triggered:
            results["messages"].append(f"❌ FAILED: PAUSE/STOP limit switch not reached within {max_steps} steps")
            print(f"\n{'='*80}")
            print(f"❌ TEST FAILED: PAUSE/STOP limit switch not reached")
            print(f"{'='*80}\n")
            return results
        
        time.sleep(0.5)  # Brief pause at max position
        
        # Step 3: Return to HOME position
        print("\nStep 3: Returning to HOME position...")
        results["messages"].append("Returning to HOME position...")
        
        # Set direction reverse
        GPIO.output(self.KEY_CATCHER_DIR_PIN, GPIO.LOW)
        
        # Move back until HOME switch is triggered
        return_steps = 0
        home_reached = False
        
        # Give a little extra buffer for return trip
        for step in range(steps_traveled + 500):
            if self.read_key_catcher_home_debounced():
                print(f"✅ Returned to HOME after {step} steps")
                results["messages"].append(f"✅ Returned to HOME position after {step} steps")
                home_reached = True
                break
            
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.HIGH)
            time.sleep(speed_delay)
            GPIO.output(self.KEY_CATCHER_STEP_PIN, GPIO.LOW)
            time.sleep(speed_delay)
            return_steps = step
        
        results["return_success"] = home_reached
        
        if not home_reached:
            results["messages"].append(f"❌ WARNING: Did not detect HOME limit switch on return (traveled {return_steps} steps)")
            print(f"⚠️  WARNING: Did not detect HOME limit switch on return")
        
        # Reset position tracking
        self.key_catcher_current_position = 0
        
        # Final result
        results["success"] = results["home_success"] and results["max_success"] and results["return_success"]
        
        print(f"\n{'='*80}")
        if results["success"]:
            print(f"✅ KEY CATCHER TEST CYCLE COMPLETE")
            print(f"   - Home → Pause: {steps_traveled} steps")
            print(f"   - Pause → Home: {return_steps} steps")
            results["messages"].append(f"✅ Test complete! Travel distance: ~{steps_traveled} steps")
        else:
            print(f"⚠️  KEY CATCHER TEST COMPLETED WITH WARNINGS")
        print(f"{'='*80}\n")
        
        return results

    def cleanup(self):
        """Clean up GPIO and disable all motors."""
        print("Disabling all motors...")
        self.enable_rotary_motor(False)
        self.enable_slider_motor(False)
        self.enable_key_catcher_motor(False)
        GPIO.cleanup()

        print("GPIO cleanup complete.")









