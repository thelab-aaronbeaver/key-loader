document.addEventListener('DOMContentLoaded', () => {
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
        btnHome.disabled = b;
        btnFwd.disabled = b;
        btnBwd.disabled = b;
        btnSliderTest.disabled = b;
        btnPicoTest.disabled = b;
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

    btnHome.addEventListener('click', async () => {
        msg.textContent = 'Homing rotary...';
        setBusy(true);
        try {
            const data = await postJSON('/api/rotary/home');
            msg.textContent = data.message || 'Homed';
        } catch (e) {
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    btnFwd.addEventListener('click', async () => {
        const deg = parseFloat(inputDeg.value) || 0;
        msg.textContent = `Moving +${deg}°...`;
        setBusy(true);
        try {
            const data = await postJSON('/api/rotary/move', { degrees: deg });
            msg.textContent = data.message || 'Moved';
        } catch (e) {
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    btnBwd.addEventListener('click', async () => {
        const deg = parseFloat(inputDeg.value) || 0;
        msg.textContent = `Moving -${deg}°...`;
        setBusy(true);
        try {
            const data = await postJSON('/api/rotary/move', { degrees: -deg });
            msg.textContent = data.message || 'Moved';
        } catch (e) {
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    btnSetZero.addEventListener('click', async () => {
        msg.textContent = 'Setting current position as zero and updating home position...';
        setBusy(true);
        try {
            const data = await postJSON('/api/rotary/set_zero');
            msg.textContent = data.message || 'Home position updated';
        } catch (e) {
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    btnSliderTest.addEventListener('click', async () => {
        sliderStatus.textContent = 'Testing slider cycle...';
        sliderStatus.className = 'status-text testing';
        msg.textContent = 'Starting slider test cycle...';
        setBusy(true);
        try {
            const data = await postJSON('/api/slider/test_cycle');
            if (data.success) {
                sliderStatus.textContent = 'Test Complete';
                sliderStatus.className = 'status-text complete';
            } else {
                sliderStatus.textContent = 'Test Failed';
                sliderStatus.className = 'status-text failed';
            }
            msg.textContent = data.message || 'Slider test completed';
        } catch (e) {
            sliderStatus.textContent = 'Test Error';
            sliderStatus.className = 'status-text failed';
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    btnPicoTest.addEventListener('click', async () => {
        picoStatus.textContent = 'Testing Pico trigger...';
        picoStatus.className = 'status-text testing';
        msg.textContent = 'Sending trigger to Pico...';
        setBusy(true);
        try {
            const data = await postJSON('/api/pico/test');
            if (data.success) {
                picoStatus.textContent = 'Trigger Sent';
                picoStatus.className = 'status-text complete';
                msg.textContent = 'Pico trigger sent successfully - check if Enter key was pressed';
            } else {
                picoStatus.textContent = 'Test Failed';
                picoStatus.className = 'status-text failed';
                msg.textContent = data.message || 'Pico test failed';
            }
        } catch (e) {
            picoStatus.textContent = 'Test Error';
            picoStatus.className = 'status-text failed';
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    async function refreshStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            // Update sensor indicators
            if (hall) {
                hall.classList.toggle('active', !!data.hall_status);
            }
            if (inductive) {
                inductive.classList.toggle('active', !!data.inductive_status);
            }
            if (smin) {
                smin.classList.toggle('active', !!data.slider_min);
            }
            if (smax) {
                smax.classList.toggle('active', !!data.slider_max);
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
            
            setBusy(!!data.is_running);
        } catch (e) {
            if (msg) msg.textContent = 'Status error: ' + e.message;
        }
    }

    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            inpStepDeg.value = cfg.step_degrees;
            inpCycles.value = cfg.cycles || 10;
            inpPause.value = cfg.pause_seconds;
            inpRotarySpeed.value = cfg.rotary_speed;
            inpRotaryAccel.value = cfg.rotary_accel_steps;
            inpRotaryDecel.value = cfg.rotary_decel_steps;
            inpInSpeed.value = cfg.slider_in_speed;
            inpOutSpeed.value = cfg.slider_out_speed;
            inpSliderAccel.value = cfg.slider_accel_steps || 20;
            inpSliderDecel.value = cfg.slider_decel_steps || 20;
        } catch (e) {
            msg.textContent = 'Load config error: ' + e.message;
        }
    }

    btnSaveCfg.addEventListener('click', async () => {
        msg.textContent = 'Saving configuration...';
        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    step_degrees: parseFloat(inpStepDeg.value),
                    cycles: parseInt(inpCycles.value, 10),
                    pause_seconds: parseFloat(inpPause.value),
                    rotary_speed: parseInt(inpRotarySpeed.value, 10),
                    rotary_accel_steps: parseInt(inpRotaryAccel.value, 10),
                    rotary_decel_steps: parseInt(inpRotaryDecel.value, 10),
                    slider_in_speed: parseInt(inpInSpeed.value, 10),
                    slider_out_speed: parseInt(inpOutSpeed.value, 10),
                    slider_accel_steps: parseInt(inpSliderAccel.value, 10),
                    slider_decel_steps: parseInt(inpSliderDecel.value, 10)
                })
            });
            const data = await res.json();
            if (!res.ok || data.success === false) throw new Error(data.message || res.statusText);
            msg.textContent = 'Configuration saved';
        } catch (e) {
            msg.textContent = 'Save config error: ' + e.message;
        }
    });

    // Initialize status elements
    sliderStatus.className = 'status-text';
    picoStatus.className = 'status-text';

    refreshStatus();
    loadConfig();
    setInterval(refreshStatus, 1000);
});


