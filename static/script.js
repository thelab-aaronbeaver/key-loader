// In file: static/script.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize WebSocket only when served over HTTP(S).
    const isFileProtocol = window.location.protocol === 'file:';
    let socket = null;
    if (!isFileProtocol) {
        try {
            socket = io();
        } catch (error) {
            console.error('Failed to initialize WebSocket connection:', error);
        }
    }

    const startButton = document.getElementById('start-button');
    const pauseButton = document.getElementById('pause-button');
    const homeButton = document.getElementById('home-button');
    const resumeButton = document.getElementById('resume-button');
    const emergencyStopButton = document.getElementById('emergency-stop-button');
    const messageDisplay = document.getElementById('system-message');
    const homedDisplay = document.getElementById('homed-status'); // May not exist
    const hallIndicator = document.getElementById('hall');
    const inductiveIndicator = document.getElementById('inductive');
    const sliderMinIndicator = document.getElementById('smin');
    const sliderMaxIndicator = document.getElementById('smax');
    const keyCatcherHomeIndicator = document.getElementById('key-catcher-home');
    const keyCatcherMaxIndicator = document.getElementById('key-catcher-max');
    const sliderStatusDisplay = document.getElementById('slider-status');
    const cyclesProgressDisplay = document.getElementById('cycles-progress');
    const currentKeyNumberDisplay = document.getElementById('current-key-number');
    const rotaryStepsDisplay = document.getElementById('rotary-steps');
    const jobStepsDisplay = document.getElementById('job-steps');
    const fullResetButton = document.getElementById('btn-full-reset');
    const keyCatcherResetButton = document.getElementById('btn-key-catcher-reset');
    const currentPositionDisplay = document.getElementById('current-position'); // May not exist
    const keywaySelect = document.getElementById('keyway');
    const pinCountSelect = document.getElementById('pin-count');
    const startingNumberInput = document.getElementById('starting-number');

    // Debug: Check if elements are found
    console.log('cyclesProgressDisplay found:', !!cyclesProgressDisplay);
    console.log('currentPositionDisplay found:', !!currentPositionDisplay);

    if (isFileProtocol) {
        if (messageDisplay) {
            messageDisplay.textContent =
                'This UI must be opened from the Flask server, not as a local file. ' +
                'Run app.py and open http://127.0.0.1:5000/';
        }
        return;
    }

    // --- ADDED: Event listener for the Home button ---
    if (homeButton) {
        homeButton.addEventListener('click', () => {
            if (messageDisplay) messageDisplay.textContent = 'Homing sequence initiated...';
            fetch('/api/home', { method: 'POST' });
        });
    }

    if (fullResetButton) {
        fullResetButton.addEventListener('click', async () => {
            if (!confirm('Full Reset will home the key catcher and move the rotary the shortest path back to step 0.\n\nContinue?')) {
                return;
            }
            if (messageDisplay) messageDisplay.textContent = 'Full reset in progress...';
            try {
                const response = await fetch('/api/full_reset', { method: 'POST' });
                const data = await response.json().catch(() => ({}));
                if (messageDisplay) {
                    messageDisplay.textContent = data.message || (response.ok ? 'Full reset complete' : 'Full reset failed');
                }
            } catch (e) {
                if (messageDisplay) messageDisplay.textContent = 'Full reset error: ' + e.message;
            }
        });
    }

    if (keyCatcherResetButton) {
        keyCatcherResetButton.addEventListener('click', async () => {
            if (messageDisplay) messageDisplay.textContent = 'Resetting key catcher...';
            try {
                const response = await fetch('/api/key_catcher/reset', { method: 'POST' });
                const data = await response.json().catch(() => ({}));
                if (messageDisplay) {
                    messageDisplay.textContent = data.message || (response.ok ? 'Key catcher reset' : 'Key catcher reset failed');
                }
            } catch (e) {
                if (messageDisplay) messageDisplay.textContent = 'Key catcher reset error: ' + e.message;
            }
        });
    }

    if (startButton) {
        startButton.addEventListener('click', async () => {
            if (startButton.textContent === 'Start Cycle') {
                // Start cycle
                if (messageDisplay) messageDisplay.textContent = 'Validating job setup...';
                // Reset cycles progress display
                if (cyclesProgressDisplay) cyclesProgressDisplay.textContent = '0 of 0';
                if (currentPositionDisplay) currentPositionDisplay.textContent = 'Position 0';

                const cyclesInput = document.getElementById('cycles');
                const cycles = cyclesInput ? parseInt(cyclesInput.value, 10) || 1 : 1;
                const startPayload = getStartPayload(cycles);
                if (!startPayload.ok) {
                    if (messageDisplay) messageDisplay.textContent = startPayload.error;
                    return;
                }

                if (messageDisplay) messageDisplay.textContent = 'Starting cycle...';
                console.log('Starting cycle with cycles:', cycles);
                try {
                    const response = await fetch('/api/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(startPayload.payload)
                    });
                    console.log('Start cycle response status:', response.status);
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        if (messageDisplay) {
                            messageDisplay.textContent = errorData.error || errorData.message || 'Unable to start cycle';
                        }
                        console.error('Start cycle error:', errorData);
                    }
                } catch (e) {
                    console.error('Start cycle fetch error:', e);
                    if (messageDisplay) messageDisplay.textContent = 'Start cycle request failed: ' + e.message;
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

    if (pauseButton) {
        pauseButton.addEventListener('click', async () => {
            const shouldResume = pauseButton.textContent === 'Resume Cycle';
            if (messageDisplay) {
                messageDisplay.textContent = shouldResume ? 'Resuming cycle...' : 'Pausing cycle...';
            }

            try {
                const endpoint = shouldResume ? '/api/cycle/resume' : '/api/cycle/pause';
                const response = await fetch(endpoint, { method: 'POST' });
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    if (messageDisplay) {
                        messageDisplay.textContent = data.error || data.message || 'Pause/Resume request failed';
                    }
                }
            } catch (e) {
                if (messageDisplay) messageDisplay.textContent = 'Pause/Resume error: ' + e.message;
            }
        });
    }

    // Resume Button (for key catcher pause)
    if (resumeButton) {
        resumeButton.addEventListener('click', async () => {
            if (messageDisplay) messageDisplay.textContent = 'Resuming cycle...';
            try {
                const response = await fetch('/api/key_catcher/resume', { method: 'POST' });
                const data = await response.json();
                if (!response.ok) {
                    if (messageDisplay) messageDisplay.textContent = 'Resume failed: ' + (data.message || data.error);
                } else {
                    if (messageDisplay) messageDisplay.textContent = data.message || 'Cycle resuming...';
                }
            } catch (e) {
                if (messageDisplay) messageDisplay.textContent = 'Resume error: ' + e.message;
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

    // HTTP polling keeps UI live during long motor moves (WebSocket alone can lag on Pi/eventlet)
    const STATUS_POLL_MS_IDLE = 500;
    const STATUS_POLL_MS_RUNNING = 250;
    let statusPollInterval = null;
    let lastRunning = false;

    function stopStatusPolling() {
        if (statusPollInterval) {
            clearInterval(statusPollInterval);
            statusPollInterval = null;
        }
    }

    function startStatusPolling(intervalMs) {
        stopStatusPolling();
        statusPollInterval = setInterval(refreshStatusFallback, intervalMs);
    }

    function syncPollRate(isRunning) {
        const ms = isRunning ? STATUS_POLL_MS_RUNNING : STATUS_POLL_MS_IDLE;
        if (!statusPollInterval) {
            startStatusPolling(ms);
            return;
        }
        if (isRunning !== lastRunning) {
            startStatusPolling(ms);
        }
    }

    // WebSocket event handlers (only if socket is available)
    if (socket) {
        socket.on('connect', function () {
            console.log('Connected to server via WebSocket');
            refreshStatusFallback();
            startStatusPolling(STATUS_POLL_MS_IDLE);
            socket.emit('request_status');
        });

        socket.on('disconnect', function () {
            console.log('Disconnected from server');
            if (messageDisplay) messageDisplay.textContent = 'Connection lost. Reconnecting...';
            startStatusPolling(STATUS_POLL_MS_IDLE);
        });

        socket.on('status_update', function (data) {
            updateUI(data);
        });
    }

    function updateUI(data) {
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
        if (keyCatcherHomeIndicator) {
            keyCatcherHomeIndicator.classList.toggle('active', data.key_catcher_home);
        }
        if (keyCatcherMaxIndicator) {
            keyCatcherMaxIndicator.classList.toggle('active', data.key_catcher_max);
        }

        // --- ADDED: Update cycle progress display ---
        if (cyclesProgressDisplay) {
            if (data.total_cycles > 0) {
                cyclesProgressDisplay.textContent = `${data.current_cycle} of ${data.total_cycles}`;
            } else {
                cyclesProgressDisplay.textContent = '0 of 0';
            }
        }
        if (currentKeyNumberDisplay) {
            if (data.current_key_number !== null && data.current_key_number !== undefined) {
                currentKeyNumberDisplay.textContent = String(data.current_key_number);
            } else {
                currentKeyNumberDisplay.textContent = '-';
            }
        }

        if (rotaryStepsDisplay) {
            rotaryStepsDisplay.textContent = String(data.rotary_current_steps ?? 0);
        }
        if (jobStepsDisplay) {
            jobStepsDisplay.textContent = String(data.job_steps_used ?? 0);
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
        if (fullResetButton) fullResetButton.disabled = isBusy || data.emergency_stop;
        if (keyCatcherResetButton) keyCatcherResetButton.disabled = isBusy;

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

        if (pauseButton) {
            if (data.emergency_stop || !data.is_running) {
                pauseButton.style.display = 'none';
            } else {
                pauseButton.style.display = 'inline-block';
                if (data.is_paused || data.pause_requested) {
                    pauseButton.textContent = 'Resume Cycle';
                    pauseButton.className = 'btn-move';
                } else {
                    pauseButton.textContent = 'Pause Cycle';
                    pauseButton.className = 'btn-back';
                }
            }
        }

        // Show/hide resume button based on key catcher pause state
        if (resumeButton) {
            if (data.key_catcher_paused) {
                resumeButton.style.display = 'inline-block';
                resumeButton.className = 'btn-move';
            } else {
                resumeButton.style.display = 'none';
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

        syncPollRate(!!data.is_running);
        lastRunning = !!data.is_running;
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

    // Load configuration on page load
    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            const cyclesInput = document.getElementById('cycles');
            if (cyclesInput && cfg.cycles) {
                cyclesInput.value = cfg.cycles;
                console.log('Loaded cycles from config:', cfg.cycles);
            }
        } catch (e) {
            console.error('Load config error:', e);
        }
    }

    function getStartPayload(cycles) {
        const keyway = keywaySelect ? String(keywaySelect.value || '').trim() : '';
        if (!keyway) {
            return { ok: false, error: 'Select a keyway before starting a cycle.' };
        }

        const pinCountValue = pinCountSelect ? String(pinCountSelect.value || '').trim() : '';
        const pinCount = parseInt(pinCountValue, 10);
        if (pinCount !== 6 && pinCount !== 7) {
            return { ok: false, error: 'Select pin count 6 or 7 before starting a cycle.' };
        }

        const startingNumberValue = startingNumberInput ? String(startingNumberInput.value || '').trim() : '';
        const startingNumber = parseInt(startingNumberValue, 10);
        if (!Number.isInteger(startingNumber) || startingNumber <= 0) {
            return { ok: false, error: 'Enter a valid starting number (positive integer).' };
        }

        return {
            ok: true,
            payload: {
                cycles,
                keyway,
                pin_count: pinCount,
                starting_number: startingNumber
            }
        };
    }

    async function loadKeyways() {
        if (!keywaySelect) return;
        try {
            const res = await fetch('/api/keyways');
            const data = await res.json().catch(() => ({}));
            const keyways = Array.isArray(data.keyways) ? data.keyways : [];
            if (!res.ok || keyways.length === 0) {
                throw new Error(data.message || 'No keyways returned');
            }

            keywaySelect.innerHTML = '';
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'Select keyway...';
            keywaySelect.appendChild(placeholder);

            for (const name of keyways) {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                keywaySelect.appendChild(option);
            }
        } catch (e) {
            console.error('Load keyways error:', e);
            if (messageDisplay) {
                messageDisplay.textContent = 'Unable to load keyway list. Check keyway.json and refresh.';
            }
        }
    }

    // Initialize: load config and start status polling (WebSocket + HTTP backup)
    loadConfig();
    loadKeyways();
    refreshStatusFallback();
    startStatusPolling(STATUS_POLL_MS_IDLE);
});