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
        
        # Test pins from hardware_controller.py
        test_pins = {
            'STEP_PIN': 20,
            'DIR_PIN': 21, 
            'ALM_PIN': 16,
            'HALL_PIN': 26,
            'INDUCTIVE_PIN': 19,
            'SLIDER_MIN_PIN': 13,
            'SLIDER_MAX_PIN': 12,
            'SLIDER_STEP_PIN': 23,
            'SLIDER_DIR_PIN': 24
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
        'HALL_PIN': 26,
        'INDUCTIVE_PIN': 19,
        'SLIDER_MIN_PIN': 13,
        'SLIDER_MAX_PIN': 12
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
        'SLIDER_STEP_PIN': 23,
        'SLIDER_DIR_PIN': 24
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
        HALL_PIN = 26
        INDUCTIVE_PIN = 19
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
                  f"Alarm: {'OK' if alm_state else 'STALL'}", end='', flush=True)
            
            time.sleep(0.1)
        
        print("\n✅ Sensor monitoring complete")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Sensor test stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Sensor Test Error: {e}")
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
            ("Sensor Reading", test_sensor_reading)
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
        print("6. For OMC closed-loop stepper: Verify differential signal wiring")
        
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
