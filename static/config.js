document.addEventListener('DOMContentLoaded', () => {
    // Initialize WebSocket connection with error handling
    let socket;
    try {
        socket = io();
    } catch (error) {
        console.error('Failed to initialize WebSocket connection:', error);
        // Fallback to polling if WebSocket fails
        setInterval(refreshStatusFallback, 1000);
    }
    const btnHome = document.getElementById('btn-home');
    const btnFwd = document.getElementById('btn-move-fwd');
    const btnBwd = document.getElementById('btn-move-bwd');
    const inputDeg = document.getElementById('degrees');
    const btnSetZero = document.getElementById('btn-set-zero');
    const btnSliderTest = document.getElementById('btn-slider-test');
    const sliderStatus = document.getElementById('slider-status');
    const btnPicoTest = document.getElementById('btn-pico-test');
    const picoStatus = document.getElementById('pico-status');
    const msg = document.getElementById('msg');
    // Config inputs
    const inpStepDeg = document.getElementById('step_degrees');
    const inpCycles = document.getElementById('cycles');
    const inpPause = document.getElementById('pause_seconds');
    const inpRotarySpeed = document.getElementById('rotary_speed');
    const inpRotaryAccel = document.getElementById('rotary_accel_steps');
    const inpRotaryDecel = document.getElementById('rotary_decel_steps');
    const inpInSpeed = document.getElementById('slider_in_speed');
    const inpOutSpeed = document.getElementById('slider_out_speed');
    const inpSliderAccel = document.getElementById('slider_accel_steps');
    const inpSliderDecel = document.getElementById('slider_decel_steps');
    const btnSaveCfg = document.getElementById('btn-save-config');
    const hall = document.getElementById('hall');
    const inductive = document.getElementById('inductive');
    const smin = document.getElementById('smin');
    const smax = document.getElementById('smax');

    function setBusy(b) {
        if (btnHome) btnHome.disabled = b;
        if (btnFwd) btnFwd.disabled = b;
        if (btnBwd) btnBwd.disabled = b;
        if (btnSliderTest) btnSliderTest.disabled = b;
        if (btnPicoTest) btnPicoTest.disabled = b;
        if (btnSetZero) btnSetZero.disabled = b;
        if (btnSaveCfg) btnSaveCfg.disabled = b;
    }

    async function postJSON(url, body) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined
        });
        let data = null;
        try { data = await res.json(); } catch { }
        if (!res.ok) throw new Error((data && data.message) || res.statusText);
        return data || {};
    }

    if (btnHome) {
        btnHome.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Homing rotary...';
            setBusy(true);
            try {
                const data = await postJSON('/api/rotary/home');
                if (msg) msg.textContent = data.message || 'Homed';
            } catch (e) {
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnFwd && inputDeg) {
        btnFwd.addEventListener('click', async () => {
            const deg = parseFloat(inputDeg.value) || 0;
            if (msg) msg.textContent = `Moving +${deg}°...`;
            setBusy(true);
            try {
                const data = await postJSON('/api/rotary/move', { degrees: deg });
                if (msg) msg.textContent = data.message || 'Moved';
            } catch (e) {
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnBwd && inputDeg) {
        btnBwd.addEventListener('click', async () => {
            const deg = parseFloat(inputDeg.value) || 0;
            if (msg) msg.textContent = `Moving -${deg}°...`;
            setBusy(true);
            try {
                const data = await postJSON('/api/rotary/move', { degrees: -deg });
                if (msg) msg.textContent = data.message || 'Moved';
            } catch (e) {
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnSetZero) {
        btnSetZero.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Setting current position as zero and updating home position...';
            setBusy(true);
            try {
                const data = await postJSON('/api/rotary/set_zero');
                if (msg) msg.textContent = data.message || 'Home position updated';
            } catch (e) {
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnSliderTest) {
        btnSliderTest.addEventListener('click', async () => {
            if (sliderStatus) {
                sliderStatus.textContent = 'Testing slider cycle...';
                sliderStatus.className = 'status-text testing';
            }
            if (msg) msg.textContent = 'Starting slider test cycle...';
            setBusy(true);
            try {
                const data = await postJSON('/api/slider/test_cycle');
                if (sliderStatus) {
                    if (data.success) {
                        sliderStatus.textContent = 'Test Complete';
                        sliderStatus.className = 'status-text complete';
                    } else {
                        sliderStatus.textContent = 'Test Failed';
                        sliderStatus.className = 'status-text failed';
                    }
                }
                if (msg) msg.textContent = data.message || 'Slider test completed';
            } catch (e) {
                if (sliderStatus) {
                    sliderStatus.textContent = 'Test Error';
                    sliderStatus.className = 'status-text failed';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnPicoTest) {
        btnPicoTest.addEventListener('click', async () => {
            if (picoStatus) {
                picoStatus.textContent = 'Testing Pico trigger...';
                picoStatus.className = 'status-text testing';
            }
            if (msg) msg.textContent = 'Sending trigger to Pico...';
            setBusy(true);
            try {
                const data = await postJSON('/api/pico/test');
                if (picoStatus) {
                    if (data.success) {
                        picoStatus.textContent = 'Trigger Sent';
                        picoStatus.className = 'status-text complete';
                    } else {
                        picoStatus.textContent = 'Test Failed';
                        picoStatus.className = 'status-text failed';
                    }
                }
                if (msg) {
                    if (data.success) {
                        msg.textContent = 'Pico trigger sent successfully - check if Enter key was pressed';
                    } else {
                        msg.textContent = data.message || 'Pico test failed';
                    }
                }
            } catch (e) {
                if (picoStatus) {
                    picoStatus.textContent = 'Test Error';
                    picoStatus.className = 'status-text failed';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    // WebSocket event handlers (only if socket is available)
    if (socket) {
        socket.on('connect', function () {
            console.log('Config page connected to server via WebSocket');
            // Request initial status
            socket.emit('request_status');
        });

        socket.on('disconnect', function () {
            console.log('Config page disconnected from server');
            if (msg) msg.textContent = 'Connection lost. Attempting to reconnect...';
        });

        socket.on('status_update', function (data) {
            updateConfigUI(data);
        });
    }

    // Fallback function for when WebSocket is not available
    async function refreshStatusFallback() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            updateConfigUI(data);
        } catch (e) {
            console.error('Status refresh error:', e);
        }
    }

    function updateConfigUI(data) {
        try {
            // Update sensor indicators
            if (hall) {
                hall.classList.toggle('active', !!data.hall_status);
                console.log('Config - Hall sensor:', data.hall_status ? 'ACTIVE' : 'INACTIVE');
            }
            if (inductive) {
                inductive.classList.toggle('active', !!data.inductive_status);
                console.log('Config - Inductive sensor:', data.inductive_status ? 'ACTIVE' : 'INACTIVE');
            }
            if (smin) {
                smin.classList.toggle('active', !!data.slider_min);
                console.log('Config - Slider MIN:', data.slider_min ? 'ACTIVE' : 'INACTIVE');
            }
            if (smax) {
                smax.classList.toggle('active', !!data.slider_max);
                console.log('Config - Slider MAX:', data.slider_max ? 'ACTIVE' : 'INACTIVE');
            }

            // Update status displays
            if (sliderStatus) {
                if (data.is_running) {
                    sliderStatus.textContent = 'Running';
                    sliderStatus.className = 'status-text testing';
                } else {
                    sliderStatus.textContent = 'Ready';
                    sliderStatus.className = 'status-text';
                }
            }

            if (picoStatus) {
                picoStatus.textContent = 'Ready';
                picoStatus.className = 'status-text';
            }

            // Update system message
            if (msg && data.system_message) {
                msg.textContent = data.system_message;
            }

            setBusy(!!data.is_running);
        } catch (error) {
            console.error('Error updating config UI:', error);
        }
    }

    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            if (inpStepDeg) inpStepDeg.value = cfg.step_degrees;
            if (inpCycles) inpCycles.value = cfg.cycles || 10;
            if (inpPause) inpPause.value = cfg.pause_seconds;
            if (inpRotarySpeed) inpRotarySpeed.value = cfg.rotary_speed;
            if (inpRotaryAccel) inpRotaryAccel.value = cfg.rotary_accel_steps;
            if (inpRotaryDecel) inpRotaryDecel.value = cfg.rotary_decel_steps;
            if (inpInSpeed) inpInSpeed.value = cfg.slider_in_speed;
            if (inpOutSpeed) inpOutSpeed.value = cfg.slider_out_speed;
            if (inpSliderAccel) inpSliderAccel.value = cfg.slider_accel_steps || 15;
            if (inpSliderDecel) inpSliderDecel.value = cfg.slider_decel_steps || 15;
        } catch (e) {
            if (msg) msg.textContent = 'Load config error: ' + e.message;
        }
    }

    if (btnSaveCfg) {
        btnSaveCfg.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Saving configuration...';
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        step_degrees: parseFloat(inpStepDeg?.value || 36),
                        cycles: parseInt(inpCycles?.value || 10, 10),
                        pause_seconds: parseFloat(inpPause?.value || 1.0),
                        rotary_speed: parseInt(inpRotarySpeed?.value || 100, 10),
                        rotary_accel_steps: parseInt(inpRotaryAccel?.value || 50, 10),
                        rotary_decel_steps: parseInt(inpRotaryDecel?.value || 50, 10),
                        slider_in_speed: parseInt(inpInSpeed?.value || 80, 10),
                        slider_out_speed: parseInt(inpOutSpeed?.value || 80, 10),
                        slider_accel_steps: parseInt(inpSliderAccel?.value || 15, 10),
                        slider_decel_steps: parseInt(inpSliderDecel?.value || 15, 10)
                    })
                });
                const data = await res.json();
                if (!res.ok || data.success === false) throw new Error(data.message || res.statusText);
                if (msg) msg.textContent = 'Configuration saved';
            } catch (e) {
                if (msg) msg.textContent = 'Save config error: ' + e.message;
            }
        });
    }

    // Initialize status elements
    if (sliderStatus) sliderStatus.className = 'status-text';
    if (picoStatus) picoStatus.className = 'status-text';

    // Load configuration and start fallback polling if WebSocket is not available
    loadConfig();
    if (!socket) {
        // Start fallback polling if WebSocket failed
        refreshStatusFallback();
    }
});


