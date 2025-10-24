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
    const btnLazerTest = document.getElementById('btn-lazer-test');
    const lazerStatus = document.getElementById('lazer-status');
    const btnLightburnPing = document.getElementById('btn-lightburn-ping');
    const btnLightburnStatus = document.getElementById('btn-lightburn-status');
    const btnLightburnStart = document.getElementById('btn-lightburn-start');
    const lightburnStatus = document.getElementById('lightburn-status');
    const lightburnStatusInfo = document.getElementById('lightburn-status-info');
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
    const inpHomeOffset = document.getElementById('home_offset');
    const inpLaserIp = document.getElementById('laser_ip');
    const inpLightburnIp = document.getElementById('lightburn_ip');
    const inpLightburnMaxWait = document.getElementById('lightburn_max_wait');
    const inpUseLightburnStatus = document.getElementById('use_lightburn_status');
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
        if (btnLazerTest) btnLazerTest.disabled = b;
        if (btnLightburnPing) btnLightburnPing.disabled = b;
        if (btnLightburnStatus) btnLightburnStatus.disabled = b;
        if (btnLightburnStart) btnLightburnStart.disabled = b;
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

    if (btnLazerTest) {
        btnLazerTest.addEventListener('click', async () => {
            if (lazerStatus) {
                lazerStatus.textContent = 'Testing UDP trigger...';
                lazerStatus.className = 'status-text testing';
            }
            if (msg) msg.textContent = 'Sending UDP trigger to LightBurn (192.168.1.170:5005)...';
            setBusy(true);
            try {
                const data = await postJSON('/api/udp/test');
                if (lazerStatus) {
                    if (data.success) {
                        lazerStatus.textContent = 'UDP Sent';
                        lazerStatus.className = 'status-text complete';
                    } else {
                        lazerStatus.textContent = 'Test Failed';
                        lazerStatus.className = 'status-text failed';
                    }
                }
                if (msg) {
                    if (data.success) {
                        msg.textContent = 'UDP trigger sent successfully - check Mac console for confirmation';
                    } else {
                        msg.textContent = data.message || 'UDP test failed - check network and listener';
                    }
                }
            } catch (e) {
                if (lazerStatus) {
                    lazerStatus.textContent = 'Test Error';
                    lazerStatus.className = 'status-text failed';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    // LightBurn test buttons
    if (btnLightburnPing) {
        btnLightburnPing.addEventListener('click', async () => {
            if (lightburnStatus) {
                lightburnStatus.textContent = 'Testing...';
                lightburnStatus.className = 'status-text testing';
            }
            if (msg) msg.textContent = 'Testing LightBurn connection...';
            setBusy(true);
            try {
                const data = await postJSON('/api/lightburn/ping');
                if (lightburnStatus) {
                    if (data.success) {
                        lightburnStatus.textContent = 'Connected';
                        lightburnStatus.className = 'status-text complete';
                    } else {
                        lightburnStatus.textContent = 'Not Connected';
                        lightburnStatus.className = 'status-text failed';
                    }
                }
                if (msg) msg.textContent = data.message;
            } catch (e) {
                if (lightburnStatus) {
                    lightburnStatus.textContent = 'Error';
                    lightburnStatus.className = 'status-text failed';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnLightburnStatus) {
        btnLightburnStatus.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Getting LightBurn status...';
            setBusy(true);
            try {
                const res = await fetch('/api/lightburn/status');
                const data = await res.json();
                if (data.success) {
                    const statusStr = JSON.stringify(data.status, null, 2);
                    const isBusy = data.is_busy ? 'BUSY' : 'IDLE';
                    if (lightburnStatusInfo) {
                        lightburnStatusInfo.textContent = `Status: ${isBusy} - ${statusStr}`;
                    }
                    if (msg) msg.textContent = `LightBurn is ${isBusy}`;
                } else {
                    if (lightburnStatusInfo) {
                        lightburnStatusInfo.textContent = 'Failed to get status';
                    }
                    if (msg) msg.textContent = data.message;
                }
            } catch (e) {
                if (lightburnStatusInfo) {
                    lightburnStatusInfo.textContent = 'Error getting status';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnLightburnStart) {
        btnLightburnStart.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Starting LightBurn job...';
            setBusy(true);
            try {
                const data = await postJSON('/api/lightburn/start');
                if (msg) msg.textContent = data.message;
            } catch (e) {
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

            if (lazerStatus) {
                lazerStatus.textContent = 'Ready';
                lazerStatus.className = 'status-text';
            }

            if (lightburnStatus) {
                lightburnStatus.textContent = 'Ready';
                lightburnStatus.className = 'status-text';
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
            if (inpHomeOffset) inpHomeOffset.value = cfg.home_offset || 0.0;
            if (inpLaserIp) inpLaserIp.value = cfg.udp_ip || '192.168.1.170';
            if (inpLightburnIp) inpLightburnIp.value = cfg.lightburn_ip || '192.168.1.170';
            if (inpLightburnMaxWait) inpLightburnMaxWait.value = cfg.lightburn_max_wait || 300;
            if (inpUseLightburnStatus) inpUseLightburnStatus.checked = cfg.use_lightburn_status !== false;
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
                        slider_decel_steps: parseInt(inpSliderDecel?.value || 15, 10),
                        home_offset: parseFloat(inpHomeOffset?.value || 0.0),
                        udp_ip: inpLaserIp?.value || '192.168.1.170',
                        lightburn_ip: inpLightburnIp?.value || '192.168.1.170',
                        lightburn_max_wait: parseInt(inpLightburnMaxWait?.value || 300, 10),
                        use_lightburn_status: inpUseLightburnStatus?.checked !== false
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
    if (lazerStatus) lazerStatus.className = 'status-text';

    // Load configuration and start fallback polling if WebSocket is not available
    loadConfig();
    if (!socket) {
        // Start fallback polling if WebSocket failed
        refreshStatusFallback();
    }
});


