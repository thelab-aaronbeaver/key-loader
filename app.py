# In file: app.py 001

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from hardware_controller import HardwareController
from lightburn_controller import LightBurnController
import time
import json
import os
import threading
import socket

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
        "cycles": 10,               # default cycle count
        "home_offset": 0.0,         # fine-tuned home position offset from hall sensor (degrees)
        "udp_enabled": True,        # enable UDP trigger to LightBurn
        "udp_ip": "127.0.0.1",      # UDP target IP (localhost for same machine)
        "udp_port": 5005,           # UDP port number
        "udp_message": "START",     # UDP trigger message
        "lightburn_enabled": True,  # enable LightBurn automation
        "lightburn_ip": "192.168.1.170",  # IP of Mac running LightBurn
        "lightburn_out_port": 19840,      # LightBurn UDP command port
        "lightburn_in_port": 19841,       # LightBurn UDP response port
        "lightburn_timeout": 2.0,         # Response timeout in seconds
        "lightburn_poll_interval": 0.1,   # Status check interval (100ms)
        "lightburn_max_wait": 300,        # Max wait for job completion (5 min)
        "use_lightburn_status": True      # Use status monitoring vs pause timer
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
            
            # Create a copy for emission, excluding non-serializable objects
            state_copy = {k: v for k, v in app_state.items() if k != "cycle_thread"}
        
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

# Initialize LightBurn controller
lb_controller = None
if config.get("lightburn_enabled", True):
    try:
        lb_controller = LightBurnController(
            target_ip=config.get("lightburn_ip", "192.168.1.170"),
            out_port=config.get("lightburn_out_port", 19840),
            in_port=config.get("lightburn_in_port", 19841),
            timeout=config.get("lightburn_timeout", 2.0)
        )
        print(f"✅ LightBurn controller initialized ({config.get('lightburn_ip')}:{config.get('lightburn_out_port')})")
    except Exception as e:
        print(f"⚠️  LightBurn controller initialization failed: {e}")

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

def send_udp_trigger():
    """Send UDP trigger message to LightBurn (legacy port 5005)."""
    if not config.get("udp_enabled", False):
        print("⏭️  UDP trigger disabled in config")
        return False
    
    try:
        udp_ip = config.get("udp_ip", "127.0.0.1")
        udp_port = config.get("udp_port", 5005)
        udp_message = config.get("udp_message", "START")
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)  # 1 second timeout
        
        # Send UDP message
        sock.sendto(udp_message.encode('utf-8'), (udp_ip, udp_port))
        sock.close()
        
        print(f"📡 UDP trigger sent to {udp_ip}:{udp_port} - Message: '{udp_message}'")
        return True
        
    except socket.timeout:
        print(f"⏱️  UDP trigger timeout to {udp_ip}:{udp_port}")
        return False
    except Exception as e:
        print(f"❌ UDP trigger error: {e}")
        return False

def start_lightburn_job():
    """Start LightBurn job via UDP automation protocol."""
    global lb_controller
    
    if not config.get("lightburn_enabled", True):
        print("⏭️  LightBurn integration disabled in config")
        return False
    
    if lb_controller is None:
        print("❌ LightBurn controller not initialized")
        return False
    
    try:
        # Start the job
        success = lb_controller.start_job()
        if success:
            print("✅ LightBurn job started successfully")
        else:
            print("❌ Failed to start LightBurn job")
        return success
    except Exception as e:
        print(f"❌ Error starting LightBurn job: {e}")
        return False

def wait_for_lightburn_completion():
    """Wait for LightBurn to complete the current job."""
    global lb_controller
    
    if not config.get("use_lightburn_status", True):
        # Fall back to pause timer if status monitoring disabled
        pause_time = max(config.get('pause_seconds', 1.0), 0)
        print(f"⏳ Using pause timer: {pause_time:.1f}s (LightBurn status monitoring disabled)")
        time.sleep(pause_time)
        return True
    
    if lb_controller is None:
        print("⚠️  LightBurn controller not available, using pause timer")
        pause_time = max(config.get('pause_seconds', 1.0), 0)
        time.sleep(pause_time)
        return True
    
    try:
        # Wait for job completion with status polling
        poll_interval = config.get("lightburn_poll_interval", 0.5)
        max_wait = config.get("lightburn_max_wait", 300)
        
        success = lb_controller.wait_for_completion(
            poll_interval=poll_interval,
            max_wait=max_wait
        )
        
        if success:
            print("✅ LightBurn job completed successfully")
        else:
            print("⚠️  LightBurn job completion timeout or error")
        
        return success
        
    except Exception as e:
        print(f"❌ Error waiting for LightBurn completion: {e}")
        # Fall back to pause timer on error
        pause_time = max(config.get('pause_seconds', 1.0), 0)
        print(f"⏳ Falling back to pause timer: {pause_time:.1f}s")
        time.sleep(pause_time)
        return False

def trigger_lightburn_job():
    """Trigger LightBurn to start the current job."""
    print(f"📡 Triggering LightBurn job...")
    
    # Send LightBurn start command via UDP automation protocol
    if config.get("lightburn_enabled", True):
        start_lightburn_job()
    
    # Also send legacy UDP trigger for backward compatibility
    send_udp_trigger()

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
    global lb_controller
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
        if 'slider_accel_steps' in data:
            config['slider_accel_steps'] = max(1, int(data['slider_accel_steps']))  # minimum 1 step
        if 'slider_decel_steps' in data:
            config['slider_decel_steps'] = max(1, int(data['slider_decel_steps']))  # minimum 1 step
        if 'rotary_speed' in data:
            config['rotary_speed'] = max(0, min(100, int(data['rotary_speed'])))  # clamp 0-100
        if 'rotary_accel_steps' in data:
            config['rotary_accel_steps'] = max(1, int(data['rotary_accel_steps']))  # minimum 1 step
        if 'rotary_decel_steps' in data:
            config['rotary_decel_steps'] = max(1, int(data['rotary_decel_steps']))  # minimum 1 step
        if 'cycles' in data:
            config['cycles'] = int(data['cycles'])
        if 'home_offset' in data:
            config['home_offset'] = float(data['home_offset'])
        if 'udp_enabled' in data:
            config['udp_enabled'] = bool(data['udp_enabled'])
        if 'udp_ip' in data:
            config['udp_ip'] = str(data['udp_ip'])
        if 'udp_port' in data:
            config['udp_port'] = int(data['udp_port'])
        if 'udp_message' in data:
            config['udp_message'] = str(data['udp_message'])
        
        # LightBurn configuration
        if 'lightburn_enabled' in data:
            config['lightburn_enabled'] = bool(data['lightburn_enabled'])
        if 'lightburn_ip' in data:
            config['lightburn_ip'] = str(data['lightburn_ip'])
        if 'lightburn_out_port' in data:
            config['lightburn_out_port'] = int(data['lightburn_out_port'])
        if 'lightburn_in_port' in data:
            config['lightburn_in_port'] = int(data['lightburn_in_port'])
        if 'lightburn_timeout' in data:
            config['lightburn_timeout'] = float(data['lightburn_timeout'])
        if 'lightburn_poll_interval' in data:
            config['lightburn_poll_interval'] = float(data['lightburn_poll_interval'])
        if 'lightburn_max_wait' in data:
            config['lightburn_max_wait'] = int(data['lightburn_max_wait'])
        if 'use_lightburn_status' in data:
            config['use_lightburn_status'] = bool(data['use_lightburn_status'])
        
        # Reinitialize LightBurn controller if settings changed
        if any(key in data for key in ['lightburn_enabled', 'lightburn_ip', 'lightburn_out_port', 'lightburn_in_port', 'lightburn_timeout']):
            if config.get("lightburn_enabled", True):
                try:
                    lb_controller = LightBurnController(
                        target_ip=config.get("lightburn_ip", "192.168.1.170"),
                        out_port=config.get("lightburn_out_port", 19840),
                        in_port=config.get("lightburn_in_port", 19841),
                        timeout=config.get("lightburn_timeout", 2.0)
                    )
                    print(f"✅ LightBurn controller reinitialized")
                except Exception as e:
                    print(f"⚠️  LightBurn controller reinit failed: {e}")
            else:
                lb_controller = None
        
        # Save to file
        if not save_config(config):
            return jsonify({"success": False, "message": "Failed to save config file"}), 500
            
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid config"}), 400
    return jsonify({"success": True, **config})

# --- ADDED: Background Cycle Function ---
def run_cycle_background(total_cycles):
    """Run the main cycle loop in a background thread."""
    cycle_start_time = time.time()
    print(f"\n{'='*80}")
    print(f"🚀 CYCLE STARTED - Processing {total_cycles} keys")
    print(f"{'='*80}\n")
    
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
            # Debug: Print cycle progress
            print(f"Cycle progress: position {current_position}, keys processed: {keys_processed} of {total_cycles}")
            
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
            target_angle = (current_position * config['step_degrees']) % 360
            safe_set_app_state("system_message", f"Searching for key at position {current_position} ({target_angle}°). Keys processed: {keys_processed} of {total_cycles}...")
            emit_status_update()
            
            if hw.read_inductive_sensor():
                # Key detected - process it
                key_start_time = time.time()
                keys_processed += 1
                current_position += 1  # Only increment position when key is processed
                safe_set_app_state("current_cycle", keys_processed)  # Update UI with keys processed count
                safe_set_app_state("system_message", f"✅ Key detected at position {current_position} ({target_angle}°). Processing key {keys_processed} of {total_cycles}...")
                emit_status_update()
                print(f"\n{'─'*80}")
                print(f"🔑 KEY {keys_processed}/{total_cycles} - Position {current_position} ({target_angle}°)")
                print(f"{'─'*80}")
                
                # Step 2: Key Processing Sequence (Optimized - Parallel Execution)
                # 1. Start LightBurn job
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. Starting LightBurn job...")
                lightburn_start_time = time.time()
                trigger_lightburn_job()
                
                # 2. PARALLEL OPERATION: Move slider while LightBurn is running
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. LightBurn running - performing slider movements...")
                
                # Move slider MAX → MIN (during LightBurn job)
                ultra_fast = config['slider_in_speed'] > 75
                in_ok = hw.slider_move_to_min(config['slider_in_speed'], accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not in_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled moving to MIN! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                # Move slider MIN → MAX (during LightBurn job)
                ultra_fast = config['slider_out_speed'] > 75
                out_ok = hw.slider_move_to_max(config['slider_out_speed'], max_pulses=50000, accel_steps=accel_steps, decel_steps=decel_steps, ultra_fast=ultra_fast)
                
                if not out_ok:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Slider motor stalled moving to MAX! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_slider_motor(False)
                    return
                
                slider_duration = time.time() - lightburn_start_time
                print(f"⏱️  Slider movements completed: {slider_duration:.2f}s (parallel with LightBurn)")
                
                # 3. Wait for LightBurn job completion (if not already done)
                if config.get("use_lightburn_status", True):
                    safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. Waiting for LightBurn job completion...")
                    wait_for_lightburn_completion()
                    lightburn_duration = time.time() - lightburn_start_time
                    print(f"⏱️  LightBurn job duration: {lightburn_duration:.2f}s")
                    
                    # Calculate time saved
                    time_saved = max(0, slider_duration - (lightburn_duration - slider_duration))
                    if time_saved > 0.1:
                        print(f"⚡ Time saved by parallel execution: {time_saved:.2f}s")
                else:
                    # Fallback: Use pause timer minus slider time already elapsed
                    pause_time = max(config.get('pause_seconds', 1.0), 0)
                    remaining_pause = max(0, pause_time - slider_duration)
                    if remaining_pause > 0:
                        safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. Waiting remaining {remaining_pause:.1f}s...")
                        time.sleep(remaining_pause)
                    lightburn_duration = lightburn_start_time + pause_time - lightburn_start_time
                    print(f"⏱️  Total pause time: {pause_time:.2f}s (slider: {slider_duration:.2f}s parallel)")
                
                # 4. Move rotary motor to next position
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles}. Moving rotary to next position...")
                move_success = hw.move_degrees(
                    config['step_degrees'], 
                    speed=config['rotary_speed'],
                    accel_steps=config['rotary_accel_steps'],
                    decel_steps=config['rotary_decel_steps']
                )
                if not move_success:
                    safe_update_app_state({
                        "system_message": "🚨 ERROR: Rotary motor stalled after key processing! Check for jams and clear obstruction. Motor paused for safety.",
                        "is_running": False
                    })
                    hw.enable_rotary_motor(False)
                    return
                
                safe_set_app_state("current_angle", target_angle)
                
                # 6. Key processing complete
                key_duration = time.time() - key_start_time
                safe_set_app_state("system_message", f"Key {keys_processed} of {total_cycles} complete. Ready for next search.")
                print(f"✅ Key {keys_processed} complete - Total time: {key_duration:.2f}s (LightBurn: {lightburn_duration:.2f}s)")
                print(f"{'─'*80}\n")
                
            else:
                # No key detected - move to next position
                current_position += 1  # Increment position counter
                safe_set_app_state("system_message", f"No key at position {current_position} ({target_angle}°). Moving to next position...")
                
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
                safe_set_app_state("system_message", f"No key at position {current_position}. Slider holding at MAX, ready for next detection.")

        # Final cleanup and statistics
        cycle_duration = time.time() - cycle_start_time
        final_state = safe_get_app_state()
        
        print(f"\n{'='*80}")
        print(f"📊 CYCLE STATISTICS")
        print(f"{'='*80}")
        print(f"Keys Processed: {keys_processed}/{total_cycles}")
        print(f"Total Cycle Time: {cycle_duration:.2f}s ({cycle_duration/60:.1f} minutes)")
        if keys_processed > 0:
            avg_per_key = cycle_duration / keys_processed
            print(f"Average Time per Key: {avg_per_key:.2f}s")
        print(f"{'='*80}\n")
        
        if final_state["is_running"]:
            if final_state["emergency_stop"]:
                safe_set_app_state("system_message", f"🚨 EMERGENCY STOP! Cycle terminated. Processed {keys_processed} keys in {cycle_duration:.1f}s.")
            elif final_state["stop_requested"]:
                safe_set_app_state("system_message", f"Cycle stopped by user. Processed {keys_processed} keys in {cycle_duration:.1f}s. Ready.")
            else:
                # All keys processed successfully - perform 2 additional step movements
                safe_set_app_state("system_message", f"All {keys_processed} keys processed. Performing 2 additional steps...")
                emit_status_update()
                
                # Rotate 2 additional steps (2 × step_degrees)
                for step in range(1, 3):
                    safe_set_app_state("system_message", f"Additional step {step} of 2 ({config['step_degrees']}°)...")
                    emit_status_update()
                    
                    move_success = hw.move_degrees(
                        config['step_degrees'],  # One step movement
                        speed=config['rotary_speed'],
                        accel_steps=config['rotary_accel_steps'],
                        decel_steps=config['rotary_decel_steps']
                    )
                    
                    if not move_success:
                        safe_set_app_state("system_message", f"⚠️ Warning: Additional step {step} failed. Cycle complete but extra steps incomplete.")
                        break
                
                safe_set_app_state("system_message", f"Cycle complete. Processed {keys_processed} keys in {cycle_duration:.1f}s. 2 additional steps complete. Ready.")
            
        # Emit final status update BEFORE resetting the cycle counters
        emit_status_update()
        
        # Now reset the cycle state
        safe_update_app_state({
            "is_running": False,
            "current_cycle": 0,
            "total_cycles": 0,
            "cycle_thread": None
        })
        
        # Don't reset stop flag if emergency stop is active
        if not final_state["emergency_stop"]:
            safe_set_app_state("stop_requested", False)
        
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
        # Apply fine-tuned home offset from config if it exists
        if config.get("home_offset", 0.0) != 0.0:
            safe_set_app_state("system_message", f"Applying fine adjustment of {config['home_offset']:.1f}°...")
            move_success = hw.move_degrees(
                config['home_offset'], 
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
        # Filter out non-serializable objects (like cycle_thread)
        return jsonify({k: v for k, v in app_state.items() if k != "cycle_thread"})

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
    
    # Save the home offset to config.json so it persists
    config["home_offset"] = home_offset
    save_config(config)
    
    if home_offset == 0.0:
        system_message = "Current position set as 0° (no offset from hall sensor). Saved to config."
    else:
        system_message = f"Current position set as 0°. Home offset: {home_offset:.1f}° from hall sensor. Saved to config."
    
    safe_update_app_state({
        "current_angle": 0,
        "is_homed": True,
        "system_message": system_message
    })
    
    final_state = safe_get_app_state()
    return jsonify({"success": True, "message": final_state["system_message"], "current_angle": final_state["current_angle"], "home_offset": config["home_offset"]})

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
        
        # Test complete - slider is now at MAX position
        safe_set_app_state("system_message", "Slider test complete. Slider is at MAX position.")
        final_state = safe_get_app_state()
        return jsonify({"success": True, "message": final_state["system_message"]})
        
    except Exception as e:
        safe_set_app_state("system_message", f"Slider test error: {str(e)}")
        final_state = safe_get_app_state()
        return jsonify({"success": False, "message": final_state["system_message"]})
    finally:
        safe_set_app_state("is_running", False)

# --- ADDED: Pico test endpoint ---
@app.route('/api/udp/test', methods=['POST'])
def api_udp_test():
    """Test UDP trigger functionality"""
    current_state = safe_get_app_state()
    if current_state["is_running"]:
        return jsonify({"success": False, "message": "Busy"}), 400
    
    try:
        safe_update_app_state({
            "is_running": True,
            "system_message": "Testing UDP trigger to LightBurn..."
        })
        
        # Send UDP trigger
        success = send_udp_trigger()
        
        if success:
            safe_set_app_state("system_message", "UDP trigger sent successfully to LightBurn")
            return jsonify({"success": True, "message": "UDP trigger sent"})
        else:
            safe_set_app_state("system_message", "UDP trigger failed - check config and network")
            return jsonify({"success": False, "message": "UDP trigger failed"})
        
    except Exception as e:
        safe_set_app_state("system_message", f"UDP test error: {str(e)}")
        final_state = safe_get_app_state()
        return jsonify({"success": False, "message": final_state["system_message"]})
    finally:
        safe_set_app_state("is_running", False)

# --- LightBurn test endpoints ---
@app.route('/api/lightburn/ping', methods=['POST'])
def api_lightburn_ping():
    """Test LightBurn connection"""
    global lb_controller
    
    if lb_controller is None:
        return jsonify({"success": False, "message": "LightBurn controller not initialized"}), 400
    
    try:
        success = lb_controller.ping()
        if success:
            return jsonify({"success": True, "message": "LightBurn is responding"})
        else:
            return jsonify({"success": False, "message": "LightBurn not responding"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/lightburn/status', methods=['GET'])
def api_lightburn_status():
    """Get LightBurn status"""
    global lb_controller
    
    if lb_controller is None:
        return jsonify({"success": False, "message": "LightBurn controller not initialized"}), 400
    
    try:
        status = lb_controller.get_status()
        is_busy = lb_controller.is_busy()
        
        return jsonify({
            "success": status is not None,
            "status": status,
            "is_busy": is_busy,
            "message": "Status retrieved successfully" if status else "Failed to get status"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/lightburn/start', methods=['POST'])
def api_lightburn_start():
    """Start LightBurn job"""
    global lb_controller
    
    if lb_controller is None:
        return jsonify({"success": False, "message": "LightBurn controller not initialized"}), 400
    
    try:
        success = start_lightburn_job()
        if success:
            return jsonify({"success": True, "message": "LightBurn job started"})
        else:
            return jsonify({"success": False, "message": "Failed to start LightBurn job"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


def status_broadcast_thread():
    """Background thread that continuously broadcasts sensor status updates."""
    print("✅ Status broadcast thread started")
    while True:
        try:
            emit_status_update()
            time.sleep(0.2)  # Update 5 times per second
        except Exception as e:
            print(f"Error in status broadcast thread: {e}")
            time.sleep(1)  # Back off on errors

if __name__ == '__main__':
    try:
        # Start background status broadcasting thread
        status_thread = threading.Thread(target=status_broadcast_thread, daemon=True)
        status_thread.start()
        
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        hw.cleanup()

