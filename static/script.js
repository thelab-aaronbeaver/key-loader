// In file: static/script.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize WebSocket connection
    const socket = io();
    const startButton = document.getElementById('start-button');
    const homeButton = document.getElementById('home-button'); // Added
    const emergencyStopButton = document.getElementById('emergency-stop-button');
    const messageDisplay = document.getElementById('system-message');
    const homedDisplay = document.getElementById('homed-status');
    const hallIndicator = document.getElementById('hall');
    const inductiveIndicator = document.getElementById('inductive');
    const sliderMinIndicator = document.getElementById('smin');
    const sliderMaxIndicator = document.getElementById('smax');
    const sliderStatusDisplay = document.getElementById('slider-status');
    const picoStatusDisplay = document.getElementById('pico-status');
    const cyclesProgressDisplay = document.getElementById('cycles-progress');
    const currentPositionDisplay = document.getElementById('current-position');

    // --- ADDED: Event listener for the Home button ---
    homeButton.addEventListener('click', () => {
        messageDisplay.textContent = 'Homing sequence initiated...';
        fetch('/api/home', { method: 'POST' });
    });

    startButton.addEventListener('click', async () => {
        if (startButton.textContent === 'Start Cycle') {
            // Start cycle
            messageDisplay.textContent = 'Starting cycle...';
            // Reset cycles progress display
            cyclesProgressDisplay.textContent = '0 of 0';
            currentPositionDisplay.textContent = 'Position 0';
            
            const cyclesInput = document.getElementById('cycles');
            const cycles = cyclesInput ? parseInt(cyclesInput.value, 10) || 1 : 1;
            try {
                await fetch('/api/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cycles }) });
            } catch (e) {
                // no-op; errors reflected via /api/status polling
            }
        } else {
            // Stop cycle
            messageDisplay.textContent = 'Stopping cycle...';
            try {
                await fetch('/api/stop', { method: 'POST' });
            } catch (e) {
                // no-op; errors reflected via /api/status polling
            }
        }
    });

    // Emergency Stop Button
    emergencyStopButton.addEventListener('click', async () => {
        if (emergencyStopButton.textContent === 'E-STOP') {
            // Activate Emergency Stop
            if (confirm('🚨 EMERGENCY STOP\n\nThis will immediately halt all motion!\n\nAre you sure you want to activate emergency stop?')) {
                messageDisplay.textContent = 'Activating emergency stop...';
                try {
                    await fetch('/api/emergency_stop', { method: 'POST' });
                } catch (e) {
                    messageDisplay.textContent = 'Emergency stop activation failed: ' + e.message;
                }
            }
        } else if (emergencyStopButton.textContent === 'Reset E-Stop') {
            // Reset Emergency Stop
            if (confirm('Reset Emergency Stop?\n\nThis will allow normal operation to resume.')) {
                messageDisplay.textContent = 'Resetting emergency stop...';
                try {
                    await fetch('/api/emergency_stop_reset', { method: 'POST' });
                } catch (e) {
                    messageDisplay.textContent = 'Emergency stop reset failed: ' + e.message;
                }
            }
        }
    });

    // WebSocket event handlers
    socket.on('connect', function() {
        console.log('Connected to server via WebSocket');
        // Request initial status
        socket.emit('request_status');
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        messageDisplay.textContent = 'Connection lost. Attempting to reconnect...';
    });

    socket.on('status_update', function(data) {
        updateUI(data);
    });

    function updateUI(data) {
        messageDisplay.textContent = data.system_message;

        // --- MODIFIED: Update homing status display ---
        if (data.is_homed) {
            homedDisplay.textContent = 'Homed';
            homedDisplay.className = 'status-value homed-yes';
        } else {
            homedDisplay.textContent = 'Not Homed';
            homedDisplay.className = 'status-value homed-no';
        }

        // Update sensor indicators
        if (hallIndicator) {
            hallIndicator.classList.toggle('active', data.hall_status);
        }
        if (inductiveIndicator) {
            inductiveIndicator.classList.toggle('active', data.inductive_status);
        }
        if (sliderMinIndicator) {
            sliderMinIndicator.classList.toggle('active', data.slider_min);
        }
        if (sliderMaxIndicator) {
            sliderMaxIndicator.classList.toggle('active', data.slider_max);
        }

        // --- ADDED: Update cycle progress display ---
        if (data.total_cycles > 0) {
            cyclesProgressDisplay.textContent = `${data.current_cycle} of ${data.total_cycles}`;
            currentPositionDisplay.textContent = `Position ${data.current_cycle}`;
        } else {
            cyclesProgressDisplay.textContent = '0 of 0';
            currentPositionDisplay.textContent = 'Position 0';
        }

        // --- MODIFIED: Update button states and text ---
        const isBusy = data.is_running;
        homeButton.disabled = isBusy;
        
        // Update start/stop button based on emergency stop state
        if (data.emergency_stop) {
            startButton.textContent = 'E-Stop Active';
            startButton.disabled = true;
            startButton.className = 'btn-stop';
            emergencyStopButton.textContent = 'Reset E-Stop';
            emergencyStopButton.className = 'btn-emergency-stop-reset';
        } else if (data.is_running) {
            startButton.textContent = 'Stop Cycle';
            startButton.disabled = false; // Allow stopping
            startButton.className = 'btn-stop'; // Add stop button styling
            emergencyStopButton.textContent = 'E-STOP';
            emergencyStopButton.className = 'btn-emergency-stop';
        } else {
            startButton.textContent = 'Start Cycle';
            startButton.disabled = !data.is_homed; // Disable if not homed
            startButton.className = 'btn-move'; // Reset to normal styling
            emergencyStopButton.textContent = 'E-STOP';
            emergencyStopButton.className = 'btn-emergency-stop';
        }
    }
});