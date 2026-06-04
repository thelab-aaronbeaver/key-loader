document.addEventListener('DOMContentLoaded', () => {
    const KEY_CATCHER_MM_PER_STEP = 3.75 / 100.0;

    function keyCatcherStepsToMm(steps) {
        return Number(steps || 0) * KEY_CATCHER_MM_PER_STEP;
    }

    function keyCatcherMmToSteps(mm) {
        return Math.max(0, Math.round(Number(mm || 0) / KEY_CATCHER_MM_PER_STEP));
    }

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
    const btnDirTest = document.getElementById('btn-dir-test');
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
    const inpFlipRotaryDirection = document.getElementById('flip_rotary_direction');
    const inpInSpeed = document.getElementById('slider_in_speed');
    const inpOutSpeed = document.getElementById('slider_out_speed');
    const inpSliderAccel = document.getElementById('slider_accel_steps');
    const inpSliderDecel = document.getElementById('slider_decel_steps');
    const inpSliderSafetyEnabled = document.getElementById('slider_safety_enabled');
    const inpSliderMaxPulses = document.getElementById('slider_max_pulses');
    const inpSliderMaxMoveSeconds = document.getElementById('slider_max_move_seconds');
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
    const keyCatcherHome = document.getElementById('key-catcher-home');
    const keyCatcherMax = document.getElementById('key-catcher-max');

    // Key catcher elements
    const btnKeyCatcherMove = document.getElementById('btn-key-catcher-move');
    const btnKeyCatcherGoto = document.getElementById('btn-key-catcher-goto');
    const btnKeyCatcherReset = document.getElementById('btn-key-catcher-reset');
    const inpKeyCatcherSteps = document.getElementById('key-catcher-steps');
    const inpKeyCatcherTarget = document.getElementById('key-catcher-target');
    const spanKeyCatcherPosition = document.getElementById('key-catcher-position');
    const spanKeyCatcherKeys = document.getElementById('key-catcher-keys');
    const keyCatcherStatus = document.getElementById('key-catcher-status');
    const inpKeyCatcherEnabled = document.getElementById('key_catcher_enabled');
    const inpKeyCatcherMmPerKey = document.getElementById('key_catcher_mm_per_key');
    const inpKeyCatcherSpeed = document.getElementById('key_catcher_speed');

    function setBusy(b) {
        if (btnHome) btnHome.disabled = b;
        if (btnFwd) btnFwd.disabled = b;
        if (btnBwd) btnBwd.disabled = b;
        if (btnDirTest) btnDirTest.disabled = b;
        if (btnSliderTest) btnSliderTest.disabled = b;
        if (btnLazerTest) btnLazerTest.disabled = b;
        if (btnLightburnPing) btnLightburnPing.disabled = b;
        if (btnLightburnStatus) btnLightburnStatus.disabled = b;
        if (btnLightburnStart) btnLightburnStart.disabled = b;
        if (btnSetZero) btnSetZero.disabled = b;
        if (btnSaveCfg) btnSaveCfg.disabled = b;
        if (btnKeyCatcherMove) btnKeyCatcherMove.disabled = b;
        if (btnKeyCatcherGoto) btnKeyCatcherGoto.disabled = b;
        if (btnKeyCatcherReset) btnKeyCatcherReset.disabled = b;
        const btnKeyCatcherTest = document.getElementById('btn-key-catcher-test');
        if (btnKeyCatcherTest) btnKeyCatcherTest.disabled = b;
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

    if (btnFwd) {
        btnFwd.addEventListener('click', async () => {
            const deg = 0.5;  // Fixed 0.5 degree increment
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

    if (btnBwd) {
        btnBwd.addEventListener('click', async () => {
            const deg = 0.5;  // Fixed 0.5 degree increment
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

                // Automatically update the home offset in the config section
                if (data.success && data.home_offset !== undefined) {
                    if (inpHomeOffset) {
                        inpHomeOffset.value = data.home_offset.toFixed(1);
                    }
                    // Reload the full config to ensure everything is in sync
                    await loadConfig();
                }
            } catch (e) {
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnDirTest) {
        btnDirTest.addEventListener('click', async () => {
            if (msg) msg.textContent = 'Running DIR signal test...';
            setBusy(true);
            try {
                const data = await postJSON('/api/rotary/dir_test', {
                    cycles: 6,
                    settle_ms: 10,
                    hold_ms: 250
                });

                const mismatchCount = (data.transitions || []).filter(
                    t => t.target_value !== t.read_settled
                ).length;

                if (msg) {
                    if (mismatchCount === 0) {
                        msg.textContent = `DIR test passed: ${data.cycles} toggles, pin ${data.pin}, all readbacks matched.`;
                    } else {
                        msg.textContent = `DIR test warning: ${mismatchCount}/${data.cycles} settled readbacks mismatched on pin ${data.pin}.`;
                    }
                }
            } catch (e) {
                if (msg) msg.textContent = 'DIR test error: ' + e.message;
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

    // Key catcher test cycle button
    const btnKeyCatcherTest = document.getElementById('btn-key-catcher-test');
    if (btnKeyCatcherTest) {
        btnKeyCatcherTest.addEventListener('click', async () => {
            if (keyCatcherStatus) {
                keyCatcherStatus.textContent = 'Testing full cycle...';
                keyCatcherStatus.className = 'status-text testing';
            }
            if (msg) msg.textContent = 'Starting key catcher test cycle (Home → Pause → Home)...';
            setBusy(true);
            try {
                const data = await postJSON('/api/key_catcher/test_cycle');
                if (keyCatcherStatus) {
                    if (data.success) {
                        keyCatcherStatus.textContent = 'Test Complete ✅';
                        keyCatcherStatus.className = 'status-text complete';
                    } else {
                        keyCatcherStatus.textContent = 'Test Failed ❌';
                        keyCatcherStatus.className = 'status-text failed';
                    }
                }
                if (msg) {
                    // Show all detailed messages
                    if (data.details && data.details.length > 0) {
                        msg.textContent = data.details.join(' | ');
                    } else {
                        msg.textContent = data.message || 'Test completed';
                    }
                }
                await updateKeyCatcherPosition();
            } catch (e) {
                if (keyCatcherStatus) {
                    keyCatcherStatus.textContent = 'Test Error';
                    keyCatcherStatus.className = 'status-text failed';
                }
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    // Key catcher button handlers
    if (btnKeyCatcherMove && inpKeyCatcherSteps) {
        btnKeyCatcherMove.addEventListener('click', async () => {
            const mm = parseFloat(inpKeyCatcherSteps.value) || 0;
            const steps = keyCatcherMmToSteps(mm);
            if (keyCatcherStatus) keyCatcherStatus.textContent = `Moving ${mm.toFixed(2)} mm...`;
            if (msg) msg.textContent = `Moving key catcher ${mm.toFixed(2)} mm (${steps} steps)...`;
            setBusy(true);
            try {
                const data = await postJSON('/api/key_catcher/move_steps', { steps: steps });
                if (data.success) {
                    if (spanKeyCatcherPosition) spanKeyCatcherPosition.textContent = keyCatcherStepsToMm(data.position).toFixed(2);
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Complete';
                } else {
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Failed';
                }
                if (msg) msg.textContent = data.message;
                await updateKeyCatcherPosition();
            } catch (e) {
                if (keyCatcherStatus) keyCatcherStatus.textContent = 'Error';
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnKeyCatcherGoto && inpKeyCatcherTarget) {
        btnKeyCatcherGoto.addEventListener('click', async () => {
            const targetMm = parseFloat(inpKeyCatcherTarget.value) || 0;
            const target = keyCatcherMmToSteps(targetMm);
            if (keyCatcherStatus) keyCatcherStatus.textContent = `Moving to ${targetMm.toFixed(2)} mm...`;
            if (msg) msg.textContent = `Moving key catcher to ${targetMm.toFixed(2)} mm (${target} steps)...`;
            setBusy(true);
            try {
                const data = await postJSON('/api/key_catcher/move_to_position', { position: target });
                if (data.success) {
                    if (spanKeyCatcherPosition) spanKeyCatcherPosition.textContent = keyCatcherStepsToMm(data.position).toFixed(2);
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Complete';
                } else {
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Failed';
                }
                if (msg) msg.textContent = data.message;
                await updateKeyCatcherPosition();
            } catch (e) {
                if (keyCatcherStatus) keyCatcherStatus.textContent = 'Error';
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    if (btnKeyCatcherReset) {
        btnKeyCatcherReset.addEventListener('click', async () => {
            if (keyCatcherStatus) keyCatcherStatus.textContent = 'Resetting to home...';
            if (msg) msg.textContent = 'Resetting key catcher to home position...';
            setBusy(true);
            try {
                const data = await postJSON('/api/key_catcher/reset');
                if (data.success) {
                    if (spanKeyCatcherPosition) spanKeyCatcherPosition.textContent = keyCatcherStepsToMm(data.position).toFixed(2);
                    if (spanKeyCatcherKeys) spanKeyCatcherKeys.textContent = '0';
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Reset Complete';
                } else {
                    if (keyCatcherStatus) keyCatcherStatus.textContent = 'Failed';
                }
                if (msg) msg.textContent = data.message;
                await updateKeyCatcherPosition();
            } catch (e) {
                if (keyCatcherStatus) keyCatcherStatus.textContent = 'Error';
                if (msg) msg.textContent = 'Error: ' + e.message;
            } finally {
                setBusy(false);
            }
        });
    }

    async function updateKeyCatcherPosition() {
        try {
            const res = await fetch('/api/key_catcher/get_position');
            const data = await res.json();
            if (data.success) {
                if (spanKeyCatcherPosition) spanKeyCatcherPosition.textContent = keyCatcherStepsToMm(data.position).toFixed(2);
                if (spanKeyCatcherKeys) spanKeyCatcherKeys.textContent = data.keys_processed;
            }
        } catch (e) {
            console.error('Error updating key catcher position:', e);
        }
    }

    let statusPollInterval = null;

    function startStatusPolling() {
        if (statusPollInterval) return;
        statusPollInterval = setInterval(refreshStatusFallback, 1000);
    }

    function stopStatusPolling() {
        if (statusPollInterval) {
            clearInterval(statusPollInterval);
            statusPollInterval = null;
        }
    }

    // WebSocket event handlers (only if socket is available)
    if (socket) {
        socket.on('connect', function () {
            console.log('Config page connected to server via WebSocket');
            stopStatusPolling();
            socket.emit('request_status');
            updateKeyCatcherPosition();
        });

        socket.on('disconnect', function () {
            console.log('Config page disconnected from server');
            if (msg) msg.textContent = 'Connection lost. Attempting to reconnect...';
            startStatusPolling();
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
            if (keyCatcherHome) {
                keyCatcherHome.classList.toggle('active', !!data.key_catcher_home);
                console.log('Config - Key Catcher HOME:', data.key_catcher_home ? 'ACTIVE' : 'INACTIVE');
            }
            if (keyCatcherMax) {
                keyCatcherMax.classList.toggle('active', !!data.key_catcher_max);
                console.log('Config - Key Catcher MAX:', data.key_catcher_max ? 'ACTIVE' : 'INACTIVE');
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
            if (inpFlipRotaryDirection) inpFlipRotaryDirection.checked = cfg.flip_rotary_direction === true;
            if (inpInSpeed) inpInSpeed.value = cfg.slider_in_speed;
            if (inpOutSpeed) inpOutSpeed.value = cfg.slider_out_speed;
            if (inpSliderAccel) inpSliderAccel.value = cfg.slider_accel_steps || 15;
            if (inpSliderDecel) inpSliderDecel.value = cfg.slider_decel_steps || 15;
            if (inpSliderSafetyEnabled) inpSliderSafetyEnabled.checked = cfg.slider_safety_enabled !== false;
            if (inpSliderMaxPulses) inpSliderMaxPulses.value = cfg.slider_max_pulses || 12000;
            if (inpSliderMaxMoveSeconds) inpSliderMaxMoveSeconds.value = cfg.slider_max_move_seconds || 3.0;
            if (inpHomeOffset) inpHomeOffset.value = cfg.home_offset || 0.0;
            if (inpLaserIp) inpLaserIp.value = cfg.udp_ip || '192.168.1.170';
            if (inpLightburnIp) inpLightburnIp.value = cfg.lightburn_ip || '192.168.1.170';
            if (inpLightburnMaxWait) inpLightburnMaxWait.value = cfg.lightburn_max_wait || 300;
            if (inpUseLightburnStatus) inpUseLightburnStatus.checked = cfg.use_lightburn_status !== false;

            // Key catcher config
            if (inpKeyCatcherEnabled) inpKeyCatcherEnabled.checked = cfg.key_catcher_enabled !== false;
            if (inpKeyCatcherMmPerKey) {
                const mmPerKey = (cfg.key_catcher_mm_per_key !== undefined)
                    ? cfg.key_catcher_mm_per_key
                    : keyCatcherStepsToMm(cfg.key_catcher_steps_per_key || 80);
                inpKeyCatcherMmPerKey.value = Number(mmPerKey).toFixed(2);
            }
            if (inpKeyCatcherSpeed) inpKeyCatcherSpeed.value = cfg.key_catcher_speed || 80;

            // Update key catcher position
            updateKeyCatcherPosition();
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
                        flip_rotary_direction: inpFlipRotaryDirection?.checked === true,
                        slider_in_speed: parseInt(inpInSpeed?.value || 80, 10),
                        slider_out_speed: parseInt(inpOutSpeed?.value || 80, 10),
                        slider_accel_steps: parseInt(inpSliderAccel?.value || 15, 10),
                        slider_decel_steps: parseInt(inpSliderDecel?.value || 15, 10),
                        slider_safety_enabled: inpSliderSafetyEnabled?.checked !== false,
                        slider_max_pulses: parseInt(inpSliderMaxPulses?.value || 12000, 10),
                        slider_max_move_seconds: parseFloat(inpSliderMaxMoveSeconds?.value || 3.0),
                        home_offset: parseFloat(inpHomeOffset?.value || 0.0),
                        udp_ip: inpLaserIp?.value || '192.168.1.170',
                        lightburn_ip: inpLightburnIp?.value || '192.168.1.170',
                        lightburn_max_wait: parseInt(inpLightburnMaxWait?.value || 300, 10),
                        use_lightburn_status: inpUseLightburnStatus?.checked !== false,
                        key_catcher_enabled: inpKeyCatcherEnabled?.checked !== false,
                        key_catcher_mm_per_key: parseFloat(inpKeyCatcherMmPerKey?.value || 3.0),
                        key_catcher_speed: parseInt(inpKeyCatcherSpeed?.value || 80, 10)
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
        refreshStatusFallback();
        startStatusPolling();
    }
});


