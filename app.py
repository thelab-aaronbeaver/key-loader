# In file: app.py 001

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from hardware_controller import HardwareController
import time
import json
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key_loader_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")
hw = HardwareController()

# --- ADDED: Thread Safety Lock ---
app_state_lock = threading.Lock()

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
    "home_offset": 0.0,  # Fine adjustment from hall sensor position
    # --- ADDED: Stop cycle flag ---
    "stop_requested": False,
    # --- ADDED: Background thread reference ---
    "cycle_thread": None,
    # --- ADDED: Emergency stop state ---
    "emergency_stop": False
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

def safe_get_app_state():
    """Thread-safe getter for app_state."""
    with app_state_lock:
        return app_state.copy()  # Return a copy to avoid external modifications

def safe_set_app_state(key, value):
    """Thread-safe setter for app_state."""
    with app_state_lock:
        app_state[key] = value

def safe_update_app_state(updates):
    """Thread-safe bulk updater for app_state."""
    with app_state_lock:
        app_state.update(updates)

def emit_status_update():
    """Emit current status to all connected WebSocket clients."""
    try:
        # Update sensor readings
        with app_state_lock:
            app_state["hall_status"] = hw.read_hall_sensor()
            app_state["inductive_status"] = hw.read_inductive_sensor()
            try:
                app_state["slider_min"] = hw.read_slider_min()
                app_state["slider_max"] = hw.read_slider_max()
            except AttributeError:
                app_state["slider_min"] = False
                app_state["slider_max"] = False
            
            # Create a copy for emission
            state_copy = app_state.copy()
        
        # Debug: Print the state being emitted
        print(f"Emitting status update - current_cycle: {state_copy.get('current_cycle', 'N/A')}, total_cycles: {state_copy.get('total_cycles', 'N/A')}")
        
        # Emit to all connected clients
        socketio.emit('status_update', state_copy)
    except Exception as e:
        print(f"Error emitting status update: {e}")

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

# --- ADDED: WebSocket Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    # Send initial status update
    emit_status_update()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('request_status')
def handle_status_request():
    """Handle status update request from client."""
    emit_status_update()

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

# --- ADDED: Background Cycle Function ---
def run_cycle_background(total_cycles):
    """Run the main cycle loop in a background thread."""
    try:
        # --- UPDATED: Start State - Check hall sensor and position slider OUT ---
        safe_set_app_state("system_message", "Starting key-driven cycle - checking initial position...")
        emit_status_update()
        
        # Check hall sensor at start position
        is_hall_active = hw.read_hall_sensor()
        if not is_hall_active:
            safe_update_app_state({
                "system_message": "ERROR: Hall sensor not active at start position (0°)!",
                "is_running": False
            })
            return
        
        # Position slider to OUT (MAX) limit switch at start
        safe_set_app_state("system_message", "Positioning slider to OUT (MAX) position...")
        accel_steps = config.get('slider_accel_steps', 15)
        decel_steps = config.get('slider_decel_steps', 15)
        ultra_fast = config['slider_out_speed'] > 75
        out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not out_ok:
            safe_update_app_state({
                "system_message": "ERROR: Slider failed to reach OUT limit switch at start.",
                "is_running": False
            })
            return
        
        safe_set_app_state("system_message", "Start state complete. Beginning key detection cycle...")

        # --- UPDATED: Key-driven cycle loop ---
        keys_processed = 0
        current_position = 0
        
        # Get initial state safely
        current_state = safe_get_app_state()
        while keys_processed < total_cycles and current_state["is_running"] and not current_state["stop_requested"] and not current_state["emergency_stop"]:
            current_position += 1
            safe_set_app_state("current_cycle", current_position)
            target_angle = (current_position * config['step_degrees']) % 360
            
            # Debug: Print cycle progress
            print(f"Cycle progress: position {current_position} of {total_cycles}, keys processed: {keys_processed}")
            
            # Emit status update to update UI
            emit_status_update()
            
            # Check for emergency stop first
            current_state = safe_get_app_state()
            if current_state["emergency_stop"]:
                safe_set_app_state("system_message", "🚨 EMERGENCY STOP ACTIVATED! Cycle terminated immediately.")
                break
            
            # Check for stop request
            if current_state["stop_requested"]:
                safe_set_app_state("system_message", "Cycle stopped by user request.")
                break
            
            # Step 1: Key Detection with Proximity Switch
            safe_set_app_state("system_message", f"Searching for key at position {current_position} of {total_cycles} ({target_angle}°)...")
            emit_status_update()
            
            if hw.read_inductive_sensor():
                # Key detected - process it
                keys_processed += 1
                safe_set_app_state("system_message", f"✅ Key detected at position {current_position} of {total_cycles} ({target_angle}°). Processing key {keys_processed} of {total_cycles}...")
                emit_status_update()
                
                # Step 2: Simultaneous Operations
                # - Trigger Pico
                send_pico_command("keyboard_enter")
                
                # - Move slider from MAX to MIN
                safe_set_app_state("system_message", f"Processing key {keys_processed} of {total_cycles}. Moving slider to MIN position...")
                ultra_fast = config['slider_in_speed'] > 75
                in_ok = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not in_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled moving to MIN! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                # - Move slider from MIN back to MAX
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. Moving slider back to MAX position...")
                ultra_fast = config['slider_out_speed'] > 75
                out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not out_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled moving to MAX! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                # - Start pause timer
                pause_time = max(config['pause_seconds'], 0)
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles} processed. Waiting {pause_time:.1f}s pause timer...")
                time.sleep(pause_time)
                
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles} complete. Ready for next position.")
                
            else:
                # No key detected - move to next position
                safe_set_app_state("system_message", f"No key at position {current_position} of {total_cycles} ({target_angle}°). Moving to next position...")
                
                # Move rotary motor by step degrees
                move_success = hw.move_degrees(
                    config['step_degrees'], 
                    speed=config['rotary_speed'],
                    accel_steps=config['rotary_accel_steps'],
                    decel_steps=config['rotary_decel_steps']
                )
                if not move_success:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Rotary motor stalled! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_rotary_motor(False)
                    return
                
                safe_set_app_state("current_angle", target_angle)
                
                # Move slider from MAX to MIN and back to MAX (continuous search pattern)
                safe_set_app_state("system_message", f"Searching pattern: Moving slider MIN→MAX at position {current_position}...")
                
                # Move to MIN
                ultra_fast = config['slider_in_speed'] > 75
                in_ok = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not in_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled during search pattern (MIN)! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                # Move back to MAX
                ultra_fast = config['slider_out_speed'] > 75
                out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not out_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled during search pattern (MAX)! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                safe_set_app_state("system_message", f"Search pattern complete at position {current_position}. Holding at MAX until next cycle.")

        # Final cleanup
        final_state = safe_get_app_state()
        if final_state["is_running"]:
            if final_state["emergency_stop"]:
                safe_set_app_state("system_message", f"🚨 EMERGENCY STOP! Cycle terminated. Processed {keys_processed} keys out of {total_cycles} positions.")
            elif final_state["stop_requested"]:
                safe_set_app_state("system_message", f"Cycle stopped by user. Processed {keys_processed} keys out of {total_cycles} positions. Ready.")
            else:
                safe_set_app_state("system_message", f"Cycle complete. Processed {keys_processed} keys out of {total_cycles} positions. Ready.")
            
        safe_update_app_state({
            "is_running": False,
            "current_cycle": 0,
            "total_cycles": 0,
            "cycle_thread": None
        })
        
        # Don't reset stop flag if emergency stop is active
        if not final_state["emergency_stop"]:
            safe_set_app_state("stop_requested", False)
            
        emit_status_update()  # Final status update
        
    except Exception as e:
        safe_update_app_state({
            "system_message": f"🚨 ERROR: Cycle failed with exception: {str(e)}",
            "is_running": False,
            "current_cycle": 0,
            "total_cycles": 0,
            "stop_requested": False,
            "cycle_thread": None
        })

# --- ADDED: Homing Route ---
@app.route('/api/home', methods=['POST'])
def home_machine():
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"error": "Cannot home while cycle is running."}), 400

    safe_update_app_state({
        "is_running": True,
        "system_message": "Homing in progress..."
    })
    
    # First, home to hall sensor position
    success = hw.home_table()
    
    if success:
        # Apply fine-tuned home offset if it exists
        current_state = safe_get_app_state()
        if current_state["home_offset"] != 0.0:
            safe_set_app_state("system_message", f"Applying fine adjustment of {current_state['home_offset']:.1f}°...")
            move_success = hw.move_degrees(
                current_state["home_offset"], 
                speed=config['rotary_speed'],
                accel_steps=config['rotary_accel_steps'],
                decel_steps=config['rotary_decel_steps']
            )
            if not move_success:
                safe_update_app_state({
                    "system_message": "ERROR: Fine adjustment failed. Motor stalled.",
                    "is_running": False
                })
                return jsonify({"success": False})
        
        safe_update_app_state({
            "is_homed": True,
            "current_angle": 0,
            "system_message": "Homing successful. Ready to start cycle."
        })
    else:
        safe_update_app_state({
            "is_homed": False,
            "system_message": "ERROR: Homing failed. Check switch and wiring."
        })

    safe_set_app_state("is_running", False)
    return jsonify({"success": success})

# --- ADDED: Stop Cycle Route ---
@app.route('/api/stop', methods=['POST'])
def stop_cycle():
    current_state = safe_get_app_state()
    if not current_state["is_running"]:
        return jsonify({"error": "No cycle is currently running."}), 400
    
    safe_update_app_state({
        "stop_requested": True,
        "system_message": "Stop requested. Cycle will stop at next safe point..."
    })
    emit_status_update()
    return jsonify({"message": "Stop requested"})

# --- ADDED: Emergency Stop Route ---
@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Immediately halt all motion - true emergency stop."""
    safe_update_app_state({
        "emergency_stop": True,
        "stop_requested": True,
        "is_running": False,
        "system_message": "🚨 EMERGENCY STOP ACTIVATED! All motion halted immediately. Check system before restarting.",
        "current_cycle": 0,
        "total_cycles": 0,
        "cycle_thread": None
    })
    
    # Immediately disable all motors
    try:
        hw.enable_rotary_motor(False)
        hw.enable_slider_motor(False)
    except Exception as e:
        print(f"Error disabling motors during E-Stop: {e}")
    
    # Emit immediate status update
    emit_status_update()
    
    return jsonify({"message": "Emergency stop activated"})

# --- ADDED: Emergency Stop Reset Route ---
@app.route('/api/emergency_stop_reset', methods=['POST'])
def emergency_stop_reset():
    """Reset emergency stop state to allow normal operation."""
    safe_update_app_state({
        "emergency_stop": False,
        "stop_requested": False,
        "system_message": "Emergency stop reset. System ready for normal operation."
    })
    emit_status_update()
    return jsonify({"message": "Emergency stop reset"})

@app.route('/api/start', methods=['POST'])
def start_cycle():
    try:
        # --- MODIFIED: Check for emergency stop state ---
        current_state = safe_get_app_state()
        
        # Debug: Print current state for troubleshooting
        print(f"Start cycle request - Current state: {current_state}")
        
        if current_state["emergency_stop"]:
            print("ERROR: Emergency stop is active")
            return jsonify({"error": "Emergency stop is active. Reset emergency stop before starting cycle."}), 400
        
        # --- MODIFIED: Check for homing status before starting ---
        if not current_state["is_homed"]:
            print("ERROR: Machine is not homed")
            return jsonify({"error": "Machine must be homed before starting a cycle."}), 400
        
        if current_state["is_running"]:
            print("ERROR: Cycle is already running")
            return jsonify({"error": "Cycle is already running."}), 400
        
        # Allow overriding cycles in request
        data = request.get_json(silent=True) or {}
        print(f"Start cycle request data: {data}")
        
        # Validate cycles parameter
        try:
            total_cycles = int(data.get('cycles', config.get('cycles', 10)))
            if total_cycles <= 0:
                print("ERROR: Invalid cycles value")
                return jsonify({"error": "Cycles must be a positive integer."}), 400
        except (ValueError, TypeError):
            print("ERROR: Invalid cycles parameter")
            return jsonify({"error": "Invalid cycles parameter. Must be a positive integer."}), 400
            
        print(f"Total cycles to run: {total_cycles}")
        
    except Exception as e:
        print(f"ERROR in start_cycle validation: {e}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

    # Set up cycle state
    safe_update_app_state({
        "is_running": True,
        "current_angle": 0,
        "current_cycle": 0,
        "total_cycles": total_cycles,
        "stop_requested": False  # Reset stop flag
    })

    # Start the cycle in a background thread
    safe_set_app_state("cycle_thread", threading.Thread(target=run_cycle_background, args=(total_cycles,)))
    current_state = safe_get_app_state()
    current_state["cycle_thread"].daemon = True  # Thread will die when main process dies
    current_state["cycle_thread"].start()
    
    # Emit initial status update
    emit_status_update()
    
    return jsonify({"message": "Cycle started in background."})

@app.route('/api/status')
def get_status():
    # Update sensor readings and return current state
    with app_state_lock:
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
        return jsonify(app_state.copy())

# --- ADDED: Rotary controls for config page ---
@app.route('/api/rotary/home', methods=['POST'])
def api_rotary_home():
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    safe_update_app_state({
        "is_running": True,
        "system_message": "Rotary homing..."
    })
    
    ok = hw.home_table()
    
    safe_update_app_state({
        "is_homed": bool(ok),
        "current_angle": 0 if ok else current_state["current_angle"],
        "system_message": "Rotary homed" if ok else "Rotary homing failed",
        "is_running": False
    })
    
    final_state = safe_get_app_state()
    return jsonify({"success": ok, "message": final_state["system_message"]})

@app.route('/api/rotary/move', methods=['POST'])
def api_rotary_move():
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    data = request.get_json(silent=True) or {}
    try:
        degrees = float(data.get("degrees", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid degrees"}), 400
    
    safe_update_app_state({
        "is_running": True,
        "system_message": f"Moving {degrees}°..."
    })
    
    ok = hw.move_degrees(
        degrees,
        speed=config['rotary_speed'],
        accel_steps=config['rotary_accel_steps'],
        decel_steps=config['rotary_decel_steps']
    )
    
    if ok:
        new_angle = (current_state["current_angle"] + degrees) % 360
        safe_set_app_state("current_angle", new_angle)
        
        # Verification: if we expect to be at 0° (within numeric wrap), hall should be active
        at_zero = abs(new_angle) < 1e-6 or abs(new_angle - 360) < 1e-6
        if at_zero:
            if not hw.read_hall_sensor():
                ok = False
                safe_set_app_state("system_message", "ERROR: Expected hall at 0°, but not detected.")
            else:
                safe_set_app_state("system_message", f"Moved {degrees}° (hall verified)")
        else:
            safe_set_app_state("system_message", f"Moved {degrees}°")
    else:
        safe_set_app_state("system_message", "Move failed")
    
    safe_set_app_state("is_running", False)
    final_state = safe_get_app_state()
    return jsonify({"success": ok, "message": final_state["system_message"], "current_angle": final_state["current_angle"]})

# --- ADDED: Set current position as zero ---
@app.route('/api/rotary/set_zero', methods=['POST'])
def api_rotary_set_zero():
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    # Calculate the offset from hall sensor position to current position
    # This represents the fine adjustment needed from the hall sensor
    home_offset = current_state["current_angle"]
    
    if home_offset == 0.0:
        system_message = "Current position set as 0° (no offset from hall sensor)."
    else:
        system_message = f"Current position set as 0°. Home offset: {home_offset:.1f}° from hall sensor."
    
    safe_update_app_state({
        "home_offset": home_offset,
        "current_angle": 0,
        "is_homed": True,
        "system_message": system_message
    })
    
    final_state = safe_get_app_state()
    return jsonify({"success": True, "message": final_state["system_message"], "current_angle": final_state["current_angle"], "home_offset": final_state["home_offset"]})

# --- ADDED: Slider test cycle ---
@app.route('/api/slider/test_cycle', methods=['POST'])
def api_slider_test_cycle():
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    safe_update_app_state({
        "is_running": True,
        "system_message": "Starting slider test cycle..."
    })
    
    try:
        # Get current slider speeds and acceleration from config
        accel_steps = config.get('slider_accel_steps', 15)
        decel_steps = config.get('slider_decel_steps', 15)
        
        # Step 1: Move to MIN limit switch
        safe_set_app_state("system_message", "Moving slider to MIN position...")
        ultra_fast = config['slider_in_speed'] > 75
        min_success = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not min_success:
            safe_set_app_state("system_message", "ERROR: Failed to reach MIN limit switch")
            final_state = safe_get_app_state()
            return jsonify({"success": False, "message": final_state["system_message"]})
        
        # Step 2: Move to MAX limit switch
        safe_set_app_state("system_message", "Moving slider to MAX position...")
        ultra_fast = config['slider_out_speed'] > 75
        max_success = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not max_success:
            safe_set_app_state("system_message", "ERROR: Failed to reach MAX limit switch")
            final_state = safe_get_app_state()
            return jsonify({"success": False, "message": final_state["system_message"]})
        
        # Step 3: Return to MIN limit switch
        safe_set_app_state("system_message", "Returning slider to MIN position...")
        ultra_fast = config['slider_in_speed'] > 75
        return_success = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
        
        if not return_success:
            safe_set_app_state("system_message", "ERROR: Failed to return to MIN limit switch")
            final_state = safe_get_app_state()
            return jsonify({"success": False, "message": final_state["system_message"]})
        
        safe_set_app_state("system_message", "Slider test cycle completed successfully")
        final_state = safe_get_app_state()
        return jsonify({"success": True, "message": final_state["system_message"]})
        
    except Exception as e:
        safe_set_app_state("system_message", f"Slider test error: {str(e)}")
        final_state = safe_get_app_state()
        return jsonify({"success": False, "message": final_state["system_message"]})
    finally:
        safe_set_app_state("is_running", False)

# --- ADDED: Pico test endpoint ---
@app.route('/api/pico/test', methods=['POST'])
def api_pico_test():
    """Test Pico trigger functionality"""
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    try:
        safe_update_app_state({
            "is_running": True,
            "system_message": "Testing Pico trigger..."
        })
        
        # Send trigger pulse to Pico
        hw.trigger_pico(duration_ms=100)
        
        safe_set_app_state("system_message", "Pico trigger sent successfully")
        return jsonify({"success": True, "message": "Pico trigger sent"})
        
    except Exception as e:
        safe_set_app_state("system_message", f"Pico test error: {str(e)}")
        final_state = safe_get_app_state()
        return jsonify({"success": False, "message": final_state["system_message"]})
    finally:
        safe_set_app_state("is_running", False)


if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        hw.cleanup()

