# In file: app.py

from flask import Flask, render_template, jsonify, request
from hardware_controller import HardwareController
import time
import json
import os

app = Flask(__name__)
hw = HardwareController()

# --- MODIFIED: Application State ---
app_state = {
    "current_angle": 0,
    "is_running": False,
    "is_homed": False, # Added homing status
    "system_message": "Machine needs to be homed.",
    "hall_status": False,
    "inductive_status": False,
    # --- ADDED: Slider limit switch states ---
    "slider_min": False,
    "slider_max": False,
    # --- ADDED: Cycle progress tracking ---
    "current_cycle": 0,
    "total_cycles": 0,
    # --- ADDED: Fine-tuned home position ---
    "home_offset": 0.0  # Fine adjustment from hall sensor position
}

# --- ADDED: Runtime configuration with JSON persistence ---
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from JSON file, create default if not exists."""
    default_config = {
        "step_degrees": 36.0,
        "pause_seconds": 1.0,       # time to hold at position (seconds)
        "slider_in_speed": 80,      # 0-100 speed scale (0=stopped, 100=750 RPM) - SERVO42C 12V OPTIMIZED
        "slider_out_speed": 80,     # 0-100 speed scale (0=stopped, 100=750 RPM) - SERVO42C 12V OPTIMIZED
        "slider_accel_steps": 15,   # steps for slider acceleration ramp-up - OPTIMIZED for SERVO42C 12V (800 pulses/rev)
        "slider_decel_steps": 15,   # steps for slider deceleration ramp-down - OPTIMIZED for SERVO42C 12V (800 pulses/rev)
        "rotary_speed": 100,        # 0-100 speed scale for rotary motor - MAXIMUM SPEED
        "rotary_accel_steps": 50,   # steps for acceleration ramp-up - reduced for faster acceleration
        "rotary_decel_steps": 50,   # steps for deceleration ramp-down - reduced for faster deceleration
        "cycles": 10                # default cycle count
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults to handle missing keys
                default_config.update(loaded_config)
                return default_config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}. Using defaults.")
    
    # Save default config if file doesn't exist
    save_config(default_config)
    return default_config

def save_config(config_dict):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving config: {e}")
        return False

# Load initial config
config = load_config()

# REMOVED: speed_to_delay() function - now handled by SERVO42C-specific function in hardware_controller.py

def send_pico_command(command):
    """Send command to Raspberry Pico via GPIO trigger pulse to emulate keyboard press."""
    print(f"📡 Sending to Pico: {command} (emulating keyboard Enter press)")
    
    # Trigger Pico via GPIO pin (100ms pulse) to emulate keyboard Enter
    hw.trigger_pico(duration_ms=100)

@app.route('/')
def index():
    return render_template('index.html')

# --- ADDED: Configuration Page ---
@app.route('/config')
def config_page():
    return render_template('config.html')

# --- ADDED: Config endpoints ---
@app.route('/api/config', methods=['GET'])
def api_get_config():
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def api_set_config():
    data = request.get_json(silent=True) or {}
    try:
        if 'step_degrees' in data:
            config['step_degrees'] = float(data['step_degrees'])
        if 'pause_seconds' in data:
            config['pause_seconds'] = float(data['pause_seconds'])
        if 'slider_in_speed' in data:
            config['slider_in_speed'] = max(0, min(100, int(data['slider_in_speed'])))  # allow up to 100 for 750 RPM maximum
        if 'slider_out_speed' in data:
            config['slider_out_speed'] = max(0, min(100, int(data['slider_out_speed'])))  # allow up to 100 for 750 RPM maximum
        if 'rotary_speed' in data:
            config['rotary_speed'] = max(0, min(100, int(data['rotary_speed'])))  # clamp 0-100
        if 'rotary_accel_steps' in data:
            config['rotary_accel_steps'] = max(1, int(data['rotary_accel_steps']))  # minimum 1 step
        if 'rotary_decel_steps' in data:
            config['rotary_decel_steps'] = max(1, int(data['rotary_decel_steps']))  # minimum 1 step
        if 'cycles' in data:
            config['cycles'] = int(data['cycles'])
        
        # Save to file
        if not save_config(config):
            return jsonify({"success": False, "message": "Failed to save config file"}), 500
            
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid config"}), 400
    return jsonify({"success": True, **config})

# --- ADDED: Homing Route ---
@app.route('/api/home', methods=['POST'])
def home_machine():
    if app_state["is_running"]:
        return jsonify({"error": "Cannot home while cycle is running."}), 400

    app_state["is_running"] = True
    app_state["system_message"] = "Homing in progress..."
    
    # First, home to hall sensor position
    success = hw.home_table()
    
    if success:
        # Apply fine-tuned home offset if it exists
        if app_state["home_offset"] != 0.0:
            app_state["system_message"] = f"Applying fine adjustment of {app_state['home_offset']:.1f}°..."
            move_success = hw.move_degrees(
                app_state["home_offset"], 
                speed=config['rotary_speed'],
                accel_steps=config['rotary_accel_steps'],
                decel_steps=config['rotary_decel_steps']
            )
            if not move_success:
                app_state["system_message"] = "ERROR: Fine adjustment failed. Motor stalled."
                app_state["is_running"] = False
                return jsonify({"success": False})
        
        app_state["is_homed"] = True
        app_state["current_angle"] = 0
        app_state["system_message"] = "Homing successful. Ready to start cycle."
    else:
        app_state["is_homed"] = False
        app_state["system_message"] = "ERROR: Homing failed. Check switch and wiring."

    app_state["is_running"] = False
    return jsonify({"success": success})


@app.route('/api/start', methods=['POST'])
def start_cycle():
    # --- MODIFIED: Check for homing status before starting ---
    if not app_state["is_homed"]:
        return jsonify({"error": "Machine must be homed before starting a cycle."}), 400
    
    if app_state["is_running"]:
        return jsonify({"error": "Cycle is already running."}), 400
    
    # Allow overriding cycles in request
    data = request.get_json(silent=True) or {}
    total_cycles = int(data.get('cycles', config.get('cycles', 10)))

    app_state["is_running"] = True
    app_state["current_angle"] = 0
    app_state["current_cycle"] = 0
    app_state["total_cycles"] = total_cycles

    # --- UPDATED: Start State - Check hall sensor and position slider OUT ---
    app_state["system_message"] = "Starting key-driven cycle - checking initial position..."
    
    # Check hall sensor at start position
    is_hall_active = hw.read_hall_sensor()
    if not is_hall_active:
        app_state["system_message"] = "ERROR: Hall sensor not active at start position (0°)!"
        app_state["is_running"] = False
        return jsonify({"error": "Hall sensor not active at start position"}), 400
    
    # Position slider to OUT (MAX) limit switch at start
    app_state["system_message"] = "Positioning slider to OUT (MAX) position..."
    accel_steps = config.get('slider_accel_steps', 15)
    decel_steps = config.get('slider_decel_steps', 15)
    ultra_fast = config['slider_out_speed'] > 75
    out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
    
    if not out_ok:
        app_state["system_message"] = "ERROR: Slider failed to reach OUT limit switch at start."
        app_state["is_running"] = False
        return jsonify({"error": "Slider failed to reach OUT limit switch at start"}), 400
    
    app_state["system_message"] = "Start state complete. Beginning key detection cycle..."

    # --- UPDATED: Key-driven cycle loop ---
    keys_processed = 0
    current_position = 0
    
    while keys_processed < total_cycles and app_state["is_running"]:
        current_position += 1
        app_state["current_cycle"] = current_position
        target_angle = (current_position * config['step_degrees']) % 360
        
        # Step 1: Key Detection with Proximity Switch
        app_state["system_message"] = f"Searching for key at position {current_position} of {total_cycles} ({target_angle}°)..."
        
        if hw.read_inductive_sensor():
            # Key detected - process it
            keys_processed += 1
            app_state["system_message"] = f"✅ Key detected at position {current_position} of {total_cycles} ({target_angle}°). Processing key {keys_processed} of {total_cycles}..."
            
            # Step 2: Simultaneous Operations
            # - Trigger Pico
            send_pico_command("keyboard_enter")
            
            # - Move slider from MAX to MIN
            app_state["system_message"] = f"Processing key {keys_processed} of {total_cycles}. Moving slider to MIN position..."
            ultra_fast = config['slider_in_speed'] > 75
            in_ok = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
            
            if not in_ok:
                app_state["system_message"] = "ERROR: Slider failed to reach MIN limit switch."
                break
            
            # - Move slider from MIN back to MAX
            app_state["system_message"] = f"Key {keys_processed} of {total_cycles}. Moving slider back to MAX position..."
            ultra_fast = config['slider_out_speed'] > 75
            out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
            
            if not out_ok:
                app_state["system_message"] = "ERROR: Slider failed to reach MAX limit switch."
                break
            
            # - Start pause timer
            pause_time = max(config['pause_seconds'], 0)
            app_state["system_message"] = f"Key {keys_processed} of {total_cycles} processed. Waiting {pause_time:.1f}s pause timer..."
            time.sleep(pause_time)
            
            app_state["system_message"] = f"Key {keys_processed} of {total_cycles} complete. Ready for next position."
            
        else:
            # No key detected - move to next position
            app_state["system_message"] = f"No key at position {current_position} of {total_cycles} ({target_angle}°). Moving to next position..."
            
            # Move rotary motor by step degrees
            move_success = hw.move_degrees(
                config['step_degrees'], 
                speed=config['rotary_speed'],
                accel_steps=config['rotary_accel_steps'],
                decel_steps=config['rotary_decel_steps']
            )
            if not move_success:
                app_state["system_message"] = "ERROR: Motor stalled during movement! Pausing motor and stopping cycle."
                hw.enable_rotary_motor(False)
                break
            
            app_state["current_angle"] = target_angle
            
            # Move slider from MAX to MIN and back to MAX (continuous search pattern)
            app_state["system_message"] = f"Searching pattern: Moving slider MIN→MAX at position {current_position}..."
            
            # Move to MIN
            ultra_fast = config['slider_in_speed'] > 75
            in_ok = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
            
            if not in_ok:
                app_state["system_message"] = "ERROR: Slider failed to reach MIN during search pattern."
                break
            
            # Move back to MAX
            ultra_fast = config['slider_out_speed'] > 75
            out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
            
            if not out_ok:
                app_state["system_message"] = "ERROR: Slider failed to reach MAX during search pattern."
                break
            
            app_state["system_message"] = f"Search pattern complete at position {current_position}. Holding at MAX until next cycle."

    if app_state["is_running"]:
        app_state["system_message"] = f"Cycle complete. Processed {keys_processed} keys out of {total_cycles} positions. Ready."
        
    app_state["is_running"] = False
    app_state["current_cycle"] = 0
    app_state["total_cycles"] = 0
    return jsonify({"message": "Cycle finished."})

@app.route('/api/status')
def get_status():
    app_state["hall_status"] = hw.read_hall_sensor()
    app_state["inductive_status"] = hw.read_inductive_sensor()
    # --- ADDED: slider switches ---
    try:
        app_state["slider_min"] = hw.read_slider_min()
        app_state["slider_max"] = hw.read_slider_max()
    except AttributeError:
        # Backward compatibility if methods not present
        app_state["slider_min"] = False
        app_state["slider_max"] = False
    return jsonify(app_state)

# --- ADDED: Rotary controls for config page ---
@app.route('/api/rotary/home', methods=['POST'])
def api_rotary_home():
    if app_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    app_state["is_running"] = True
    app_state["system_message"] = "Rotary homing..."
    ok = hw.home_table()
    app_state["is_homed"] = bool(ok)
    app_state["current_angle"] = 0 if ok else app_state["current_angle"]
    app_state["system_message"] = "Rotary homed" if ok else "Rotary homing failed"
    app_state["is_running"] = False
    return jsonify({"success": ok, "message": app_state["system_message"]})

@app.route('/api/rotary/move', methods=['POST'])
def api_rotary_move():
    if app_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    data = request.get_json(silent=True) or {}
    try:
        degrees = float(data.get("degrees", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid degrees"}), 400
    app_state["is_running"] = True
    app_state["system_message"] = f"Moving {degrees}°..."
    ok = hw.move_degrees(
        degrees,
        speed=config['rotary_speed'],
        accel_steps=config['rotary_accel_steps'],
        decel_steps=config['rotary_decel_steps']
    )
    if ok:
        app_state["current_angle"] = (app_state["current_angle"] + degrees) % 360
        # Verification: if we expect to be at 0° (within numeric wrap), hall should be active
        at_zero = abs(app_state["current_angle"]) < 1e-6 or abs(app_state["current_angle"] - 360) < 1e-6
        if at_zero:
            if not hw.read_hall_sensor():
                ok = False
                app_state["system_message"] = "ERROR: Expected hall at 0°, but not detected."
            else:
                app_state["system_message"] = f"Moved {degrees}° (hall verified)"
        else:
            app_state["system_message"] = f"Moved {degrees}°"
    else:
        app_state["system_message"] = "Move failed"
    app_state["is_running"] = False
    return jsonify({"success": ok, "message": app_state["system_message"], "current_angle": app_state["current_angle"]})

# --- ADDED: Set current position as zero ---
@app.route('/api/rotary/set_zero', methods=['POST'])
def api_rotary_set_zero():
    if app_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    # Calculate the offset from hall sensor position to current position
    # This represents the fine adjustment needed from the hall sensor
    app_state["home_offset"] = app_state["current_angle"]
    app_state["current_angle"] = 0
    app_state["is_homed"] = True
    
    if app_state["home_offset"] == 0.0:
        app_state["system_message"] = "Current position set as 0° (no offset from hall sensor)."
    else:
        app_state["system_message"] = f"Current position set as 0°. Home offset: {app_state['home_offset']:.1f}° from hall sensor."
    
    return jsonify({"success": True, "message": app_state["system_message"], "current_angle": app_state["current_angle"], "home_offset": app_state["home_offset"]})

# --- ADDED: Slider test cycle ---
@app.route('/api/slider/test_cycle', methods=['POST'])
def api_slider_test_cycle():
    if app_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    app_state["is_running"] = True
    app_state["system_message"] = "Starting slider test cycle..."
    
    try:
        # Get current slider speeds and acceleration from config
        accel_steps = config.get('slider_accel_steps', 15)
        decel_steps = config.get('slider_decel_steps', 15)
        
        # Step 1: Move to MIN limit switch
        app_state["system_message"] = "Moving slider to MIN position..."
        ultra_fast = config['slider_in_speed'] > 75
        min_success = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not min_success:
            app_state["system_message"] = "ERROR: Failed to reach MIN limit switch"
            return jsonify({"success": False, "message": app_state["system_message"]})
        
        # Step 2: Move to MAX limit switch
        app_state["system_message"] = "Moving slider to MAX position..."
        ultra_fast = config['slider_out_speed'] > 75
        max_success = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not max_success:
            app_state["system_message"] = "ERROR: Failed to reach MAX limit switch"
            return jsonify({"success": False, "message": app_state["system_message"]})
        
        # Step 3: Return to MIN limit switch
        app_state["system_message"] = "Returning slider to MIN position..."
        ultra_fast = config['slider_in_speed'] > 75
        return_success = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not return_success:
            app_state["system_message"] = "ERROR: Failed to return to MIN limit switch"
            return jsonify({"success": False, "message": app_state["system_message"]})
        
        app_state["system_message"] = "Slider test cycle completed successfully"
        return jsonify({"success": True, "message": app_state["system_message"]})
        
    except Exception as e:
        app_state["system_message"] = f"Slider test error: {str(e)}"
        return jsonify({"success": False, "message": app_state["system_message"]})
    finally:
        app_state["is_running"] = False

# --- ADDED: Pico test endpoint ---
@app.route('/api/pico/test', methods=['POST'])
def api_pico_test():
    """Test Pico trigger functionality"""
    if app_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    try:
        app_state["is_running"] = True
        app_state["system_message"] = "Testing Pico trigger..."
        
        # Send trigger pulse to Pico
        hw.trigger_pico(duration_ms=100)
        
        app_state["system_message"] = "Pico trigger sent successfully"
        return jsonify({"success": True, "message": "Pico trigger sent"})
        
    except Exception as e:
        app_state["system_message"] = f"Pico test error: {str(e)}"
        return jsonify({"success": False, "message": app_state["system_message"]})
    finally:
        app_state["is_running"] = False


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        hw.cleanup()
