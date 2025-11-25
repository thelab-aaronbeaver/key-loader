#!/usr/bin/env python3
"""
GPIO Diagnostic Test Script for Key Loader
This script helps diagnose motor and sensor issues
"""

import RPi.GPIO as GPIO
import time
import sys

def test_gpio_basic():
    """Test basic GPIO functionality"""
    print("🔧 Testing Basic GPIO Functionality...")
    
    try:
        # Test GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        print("✅ GPIO mode set to BCM")
        
        # Test pins from hardware_controller.py (CURRENT CONFIGURATION)
        test_pins = {
            'STEP_PIN': 20,
            'DIR_PIN': 21,
            'ENABLE_PIN': 12,
            'ALM_PIN': 16,
            'HALL_PIN': 27,
            'INDUCTIVE_PIN': 22,
            'SLIDER_MIN_PIN': 4,
            'SLIDER_MAX_PIN': 17,
            'SLIDER_STEP_PIN': 23,
            'SLIDER_DIR_PIN': 24,
            'SLIDER_ENABLE_PIN': 25,
            'KEY_CATCHER_STEP_PIN': 26,
            'KEY_CATCHER_DIR_PIN': 19,
            'KEY_CATCHER_ENABLE_PIN': 13,
            'KEY_CATCHER_HOME_PIN': 5,
            'KEY_CATCHER_MAX_PIN': 6
        }
        
        print("\n📌 Pin Configuration:")
        for name, pin in test_pins.items():
            print(f"  {name}: GPIO {pin}")
            
        return True
        
    except Exception as e:
        print(f"❌ GPIO Setup Error: {e}")
        return False

def test_input_pins():
    """Test all input pins (sensors and limit switches)"""
    print("\n🔍 Testing Input Pins (Sensors & Limit Switches)...")
    
    input_pins = {
        'ALM_PIN': 16,
        'HALL_PIN': 27,
        'INDUCTIVE_PIN': 22,
        'SLIDER_MIN_PIN': 4,
        'SLIDER_MAX_PIN': 17,
        'KEY_CATCHER_HOME_PIN': 5,
        'KEY_CATCHER_MAX_PIN': 6
    }
    
    try:
        # Setup input pins with pull-up
        for name, pin in input_pins.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"✅ {name} (GPIO {pin}) configured as input with pull-up")
        
        print("\n📊 Current Input States:")
        for name, pin in input_pins.items():
            state = GPIO.input(pin)
            status = "HIGH (3.3V)" if state else "LOW (0V)"
            print(f"  {name} (GPIO {pin}): {status}")
            
        return True
        
    except Exception as e:
        print(f"❌ Input Pin Test Error: {e}")
        return False

def test_output_pins():
    """Test all output pins (motor control)"""
    print("\n⚡ Testing Output Pins (Motor Control)...")
    
    output_pins = {
        'STEP_PIN': 20,
        'DIR_PIN': 21,
        'ENABLE_PIN': 12,
        'SLIDER_STEP_PIN': 23,
        'SLIDER_DIR_PIN': 24,
        'SLIDER_ENABLE_PIN': 25,
        'KEY_CATCHER_STEP_PIN': 26,
        'KEY_CATCHER_DIR_PIN': 19,
        'KEY_CATCHER_ENABLE_PIN': 13
    }
    
    try:
        # Setup output pins
        for name, pin in output_pins.items():
            GPIO.setup(pin, GPIO.OUT)
            print(f"✅ {name} (GPIO {pin}) configured as output")
        
        print("\n🔄 Testing Output Toggle...")
        for name, pin in output_pins.items():
            print(f"  Testing {name} (GPIO {pin}):")
            
            # Toggle pin a few times
            for i in range(3):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.1)
                print(f"    Toggle {i+1}/3")
            
            print(f"  ✅ {name} toggle test complete")
            
        return True
        
    except Exception as e:
        print(f"❌ Output Pin Test Error: {e}")
        return False

def test_motor_step_sequence():
    """Test motor step sequence"""
    print("\n🎯 Testing Motor Step Sequence...")
    
    try:
        STEP_PIN = 20
        DIR_PIN = 21
        
        # Set direction
        GPIO.output(DIR_PIN, GPIO.HIGH)
        print("✅ Direction set to HIGH (clockwise)")
        
        # Send a few steps
        print("🔄 Sending 10 test steps...")
        for i in range(10):
            GPIO.output(STEP_PIN, GPIO.HIGH)
            time.sleep(0.001)  # 1ms pulse
            GPIO.output(STEP_PIN, GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
            print(f"  Step {i+1}/10")
        
        print("✅ Motor step sequence test complete")
        return True
        
    except Exception as e:
        print(f"❌ Motor Step Test Error: {e}")
        return False

def test_sensor_reading():
    """Test sensor reading with user interaction"""
    print("\n👁️ Testing Sensor Reading...")
    print("This will monitor sensors for 10 seconds. Trigger sensors manually to test.")
    
    try:
        HALL_PIN = 27
        INDUCTIVE_PIN = 22
        ALM_PIN = 16
        
        print("Monitoring sensors for 10 seconds...")
        print("Press Ctrl+C to stop early")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            hall_state = GPIO.input(HALL_PIN)
            inductive_state = GPIO.input(INDUCTIVE_PIN)
            alm_state = GPIO.input(ALM_PIN)
            
            print(f"\rHall: {'ACTIVE' if not hall_state else 'INACTIVE'} | "
                  f"Inductive: {'ACTIVE' if not inductive_state else 'INACTIVE'} | "
                  f"Rotary Alarm: {'OK' if alm_state else 'STALL'}    ", end='', flush=True)
            
            time.sleep(0.1)
        
        print("\n✅ Sensor monitoring complete")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Sensor test stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Sensor Test Error: {e}")
        return False

def test_inductive_sensor_detailed():
    """Detailed test for inductive sensor on GPIO 22"""
    print("\n🔍 DETAILED INDUCTIVE SENSOR TEST (GPIO 22)...")
    
    try:
        INDUCTIVE_PIN = 22
        
        # Setup with pull-down (due to weak voltage levels: 0.7V/0.3V)
        GPIO.setup(INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print(f"✅ Inductive sensor pin (GPIO {INDUCTIVE_PIN}) configured with pull-down")
        
        # Check initial state
        initial_state = GPIO.input(INDUCTIVE_PIN)
        print(f"📊 Initial state: {'HIGH (inactive)' if initial_state else 'LOW (active)'}")
        
        # Alternative configurations to test
        print("\n🔄 Testing different pull resistor configurations...")
        
        # Test with pull-down
        GPIO.setup(INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        time.sleep(0.1)
        pulldown_state = GPIO.input(INDUCTIVE_PIN)
        print(f"  With PULL-DOWN: {'HIGH' if pulldown_state else 'LOW'}")
        
        # Test with no pull resistor
        GPIO.setup(INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
        time.sleep(0.1)
        float_state = GPIO.input(INDUCTIVE_PIN)
        print(f"  With NO PULL (floating): {'HIGH' if float_state else 'LOW'}")
        
        # Reset to pull-up (standard configuration)
        GPIO.setup(INDUCTIVE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.1)
        
        print("\n👁️ Monitoring inductive sensor for 15 seconds...")
        print("   Bring a metal object within 4mm to test detection")
        print("   Press Ctrl+C to stop early\n")
        
        last_state = None
        trigger_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 15:
            current_state = GPIO.input(INDUCTIVE_PIN)
            
            # Detect state changes
            if last_state is not None and current_state != last_state:
                trigger_count += 1
                if not current_state:  # Went LOW (active)
                    print(f"✨ DETECTED! Metal object detected at {time.time() - start_time:.2f}s")
                else:  # Went HIGH (inactive)
                    print(f"   Released at {time.time() - start_time:.2f}s")
            
            last_state = current_state
            
            # Display status
            status = "🟢 ACTIVE (detecting)" if not current_state else "⚪ INACTIVE"
            elapsed = int(time.time() - start_time)
            print(f"\r{status} | Time: {elapsed}s | Triggers: {trigger_count}  ", end='', flush=True)
            
            time.sleep(0.05)  # 50ms sampling
        
        print(f"\n\n📊 Test Results:")
        print(f"   Total triggers detected: {trigger_count}")
        print(f"   Final state: {'ACTIVE (LOW)' if not current_state else 'INACTIVE (HIGH)'}")
        
        if trigger_count == 0:
            print("\n⚠️ WARNING: No triggers detected!")
            print("   Possible issues:")
            print("   1. Sensor not powered (check 12V supply)")
            print("   2. Wrong wiring (check signal wire to GPIO 22)")
            print("   3. Voltage divider issue (should be 10kΩ + 3.3kΩ)")
            print("   4. Defective sensor")
            print("   5. Metal object too far (must be within 4mm)")
            print("\n   📊 Your reported voltages: 0.7V (idle) / 0.3V (active)")
            print("   These are TOO LOW! See inductive_sensor_fix.md for solutions.")
            print("   Quick fix: Add 10kΩ pull-up from sensor output to +12V")
        else:
            print("✅ Sensor is detecting!")
            print("   Note: Voltage levels (0.7V/0.3V) are borderline.")
            print("   For better reliability, add 10kΩ pull-up to +12V")
            print("   See inductive_sensor_fix.md for details")
        
        return trigger_count > 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Inductive sensor test stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Inductive Sensor Test Error: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔧 Key Loader GPIO Diagnostic Tool")
    print("=" * 50)
    
    try:
        # Run all tests
        tests = [
            ("Basic GPIO", test_gpio_basic),
            ("Input Pins", test_input_pins),
            ("Output Pins", test_output_pins),
            ("Motor Steps", test_motor_step_sequence),
            ("Sensor Reading", test_sensor_reading),
            ("Inductive Sensor (Detailed)", test_inductive_sensor_detailed)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print(f"\n{'='*50}")
        print("📋 DIAGNOSTIC SUMMARY")
        print(f"{'='*50}")
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:20} {status}")
        
        # Recommendations
        print(f"\n💡 TROUBLESHOOTING RECOMMENDATIONS:")
        print("1. If GPIO setup fails: Check RPi.GPIO installation and permissions")
        print("2. If input pins show wrong states: Check wiring and pull-up resistors")
        print("3. If output pins don't toggle: Check wiring to motor drivers")
        print("4. If motor doesn't move: Check power supply and driver connections")
        print("5. If sensors don't respond: Check sensor wiring and power")
        print("6. For inductive sensor (GPIO 22):")
        print("   - Check 12V power supply to sensor")
        print("   - Verify voltage divider: 10kΩ (sensor → GPIO) + 3.3kΩ (GPIO → GND)")
        print("   - Metal object must be within 4mm of sensor")
        print("   - Sensor output should be 12V (NPN NO type)")
        print("7. For CL57T closed-loop stepper: Verify differential signal wiring")
        print("8. For MKS SERVO42C drivers: Check 12V power and 4x microstepping")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
    finally:
        try:
            GPIO.cleanup()
            print("\n🧹 GPIO cleanup complete")
        except:
            pass

if __name__ == "__main__":
    main()
