# In file: app.py

from flask import Flask, render_template, jsonify, request
from hardware_controller import HardwareController
import time

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
    "slider_max": False
}

@app.route('/')
def index():
    return render_template('index.html')

# --- ADDED: Configuration Page ---
@app.route('/config')
def config_page():
    return render_template('config.html')

# --- ADDED: Homing Route ---
@app.route('/api/home', methods=['POST'])
def home_machine():
    if app_state["is_running"]:
        return jsonify({"error": "Cannot home while cycle is running."}), 400

    app_state["is_running"] = True
    app_state["system_message"] = "Homing in progress..."
    
    success = hw.home_table()
    
    if success:
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
    
    app_state["is_running"] = True
    app_state["current_angle"] = 0

    for i in range(1, 11):
        target_angle = i * 36
        app_state["system_message"] = f"Moving to position {i} ({target_angle}°)..."
        
        move_success = hw.move_degrees(36)
        if not move_success:
            app_state["system_message"] = "ERROR: Motor stalled during movement!"
            break 
        
        app_state["current_angle"] = target_angle
        time.sleep(0.5)

        is_hall_active = hw.read_hall_sensor()
        if not is_hall_active:
            app_state["system_message"] = f"ERROR: Position mismatch at {target_angle}°!"
            break

        if hw.read_inductive_sensor():
            app_state["system_message"] = f"✅ Key detected at {target_angle}°. Triggering."
            # TODO: Send command to Pico
            time.sleep(1)
        else:
            app_state["system_message"] = f"No key at {target_angle}°. Moving on."

    if app_state["is_running"]:
        app_state["system_message"] = "Cycle complete. Ready."
        
    app_state["is_running"] = False
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
    ok = hw.move_degrees(degrees)
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
    # Trust the operator: set current as absolute zero
    app_state["current_angle"] = 0
    app_state["is_homed"] = True
    app_state["system_message"] = "Current position set as 0°."
    return jsonify({"success": True, "message": app_state["system_message"], "current_angle": app_state["current_angle"]})


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        hw.cleanup()
