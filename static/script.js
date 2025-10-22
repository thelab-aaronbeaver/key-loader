// In file: static/script.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize WebSocket connection with error handling
    let socket;
    try {
        socket = io();
    } catch (error) {
        console.error('Failed to initialize WebSocket connection:', error);
    }

    const startButton = document.getElementById('start-button');
    const homeButton = document.getElementById('home-button');
    const emergencyStopButton = document.getElementById('emergency-stop-button');
    const messageDisplay = document.getElementById('system-message');
    const homedDisplay = document.getElementById('homed-status'); // May not exist
    const hallIndicator = document.getElementById('hall');
    const inductiveIndicator = document.getElementById('inductive');
    const sliderMinIndicator = document.getElementById('smin');
    const sliderMaxIndicator = document.getElementById('smax');
    const sliderStatusDisplay = document.getElementById('slider-status');
    const picoStatusDisplay = document.getElementById('pico-status');
    const cyclesProgressDisplay = document.getElementById('cycles-progress');
    const currentPositionDisplay = document.getElementById('current-position'); // May not exist

    // Debug: Check if elements are found
    console.log('cyclesProgressDisplay found:', !!cyclesProgressDisplay);
    console.log('currentPositionDisplay found:', !!currentPositionDisplay);

    // --- ADDED: Event listener for the Home button ---
    if (homeButton) {
        homeButton.addEventListener('click', () => {
            if (messageDisplay) messageDisplay.textContent = 'Homing sequence initiated...';
            fetch('/api/home', { method: 'POST' });
        });
    }

    if (startButton) {
        startButton.addEventListener('click', async () => {
            if (startButton.textContent === 'Start Cycle') {
                // Start cycle
                if (messageDisplay) messageDisplay.textContent = 'Starting cycle...';
                // Reset cycles progress display
                if (cyclesProgressDisplay) cyclesProgressDisplay.textContent = '0 of 0';
                if (currentPositionDisplay) currentPositionDisplay.textContent = 'Position 0';

                const cyclesInput = document.getElementById('cycles');
                const cycles = cyclesInput ? parseInt(cyclesInput.value, 10) || 1 : 1;
                console.log('Starting cycle with cycles:', cycles);
                try {
                    const response = await fetch('/api/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ cycles })
                    });
                    console.log('Start cycle response status:', response.status);
                    if (!response.ok) {
                        const errorData = await response.json();
                        console.error('Start cycle error:', errorData);
                    }
                } catch (e) {
                    console.error('Start cycle fetch error:', e);
                    // no-op; errors reflected via /api/status polling
                }
            } else {
                // Stop cycle
                if (messageDisplay) messageDisplay.textContent = 'Stopping cycle...';
                try {
                    await fetch('/api/stop', { method: 'POST' });
                } catch (e) {
                    // no-op; errors reflected via /api/status polling
                }
            }
        });
    }

    // Emergency Stop Button
    if (emergencyStopButton) {
        emergencyStopButton.addEventListener('click', async () => {
            if (emergencyStopButton.textContent === 'E-STOP') {
                // Activate Emergency Stop
                if (confirm('🚨 EMERGENCY STOP\n\nThis will immediately halt all motion!\n\nAre you sure you want to activate emergency stop?')) {
                    if (messageDisplay) messageDisplay.textContent = 'Activating emergency stop...';
                    try {
                        await fetch('/api/emergency_stop', { method: 'POST' });
                    } catch (e) {
                        if (messageDisplay) messageDisplay.textContent = 'Emergency stop activation failed: ' + e.message;
                    }
                }
            } else if (emergencyStopButton.textContent === 'Reset E-Stop') {
                // Reset Emergency Stop
                if (confirm('Reset Emergency Stop?\n\nThis will allow normal operation to resume.')) {
                    if (messageDisplay) messageDisplay.textContent = 'Resetting emergency stop...';
                    try {
                        await fetch('/api/emergency_stop_reset', { method: 'POST' });
                    } catch (e) {
                        if (messageDisplay) messageDisplay.textContent = 'Emergency stop reset failed: ' + e.message;
                    }
                }
            }
        });
    }

    // WebSocket event handlers (only if socket is available)
    if (socket) {
        socket.on('connect', function () {
            console.log('Connected to server via WebSocket');
            // Request initial status
            socket.emit('request_status');
        });

        socket.on('disconnect', function () {
            console.log('Disconnected from server');
            if (messageDisplay) messageDisplay.textContent = 'Connection lost. Attempting to reconnect...';
        });

        socket.on('status_update', function (data) {
            updateUI(data);
        });
    }

    function updateUI(data) {
        console.log('updateUI called with data:', data);
        if (messageDisplay) messageDisplay.textContent = data.system_message;

        // --- MODIFIED: Update homing status display (only if element exists) ---
        if (homedDisplay) {
            if (data.is_homed) {
                homedDisplay.textContent = 'Homed';
                homedDisplay.className = 'status-value homed-yes';
            } else {
                homedDisplay.textContent = 'Not Homed';
                homedDisplay.className = 'status-value homed-no';
            }
        }

        // Update sensor indicators
        if (hallIndicator) {
            hallIndicator.classList.toggle('active', data.hall_status);
            console.log('Hall sensor:', data.hall_status ? 'ACTIVE' : 'INACTIVE');
        }
        if (inductiveIndicator) {
            inductiveIndicator.classList.toggle('active', data.inductive_status);
            console.log('Inductive sensor:', data.inductive_status ? 'ACTIVE' : 'INACTIVE');
        }
        if (sliderMinIndicator) {
            sliderMinIndicator.classList.toggle('active', data.slider_min);
            console.log('Slider MIN:', data.slider_min ? 'ACTIVE' : 'INACTIVE');
        }
        if (sliderMaxIndicator) {
            sliderMaxIndicator.classList.toggle('active', data.slider_max);
            console.log('Slider MAX:', data.slider_max ? 'ACTIVE' : 'INACTIVE');
        }

        // --- ADDED: Update cycle progress display ---
        if (cyclesProgressDisplay) {
            console.log('Updating cycles progress:', data.current_cycle, 'of', data.total_cycles);
            if (data.total_cycles > 0) {
                cyclesProgressDisplay.textContent = `${data.current_cycle} of ${data.total_cycles}`;
            } else {
                cyclesProgressDisplay.textContent = '0 of 0';
            }
        } else {
            console.log('cyclesProgressDisplay element not found!');
        }

        if (currentPositionDisplay) {
            if (data.total_cycles > 0) {
                currentPositionDisplay.textContent = `Position ${data.current_cycle}`;
            } else {
                currentPositionDisplay.textContent = 'Position 0';
            }
        }

        // --- MODIFIED: Update button states and text ---
        const isBusy = data.is_running;
        if (homeButton) homeButton.disabled = isBusy;

        // Update start/stop button based on emergency stop state
        if (startButton) {
            if (data.emergency_stop) {
                startButton.textContent = 'E-Stop Active';
                startButton.disabled = true;
                startButton.className = 'btn-stop';
            } else if (data.is_running) {
                startButton.textContent = 'Stop Cycle';
                startButton.disabled = false; // Allow stopping
                startButton.className = 'btn-stop'; // Add stop button styling
            } else {
                startButton.textContent = 'Start Cycle';
                startButton.disabled = !data.is_homed; // Disable if not homed
                startButton.className = 'btn-move'; // Reset to normal styling
            }
        }

        if (emergencyStopButton) {
            if (data.emergency_stop) {
                emergencyStopButton.textContent = 'Reset E-Stop';
                emergencyStopButton.className = 'btn-emergency-stop-reset';
            } else {
                emergencyStopButton.textContent = 'E-STOP';
                emergencyStopButton.className = 'btn-emergency-stop';
            }
        }
    }

    // Fallback function for when WebSocket is not available
    async function refreshStatusFallback() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            updateUI(data);
        } catch (e) {
            console.error('Status refresh error:', e);
        }
    }

    // Start fallback polling if WebSocket is not available
    if (!socket) {
        console.log('WebSocket not available, using polling fallback');
        refreshStatusFallback(); // Initial load
        setInterval(refreshStatusFallback, 1000); // Poll every second
    }
});