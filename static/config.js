document.addEventListener('DOMContentLoaded', () => {
    const btnHome = document.getElementById('btn-home');
    const btnFwd = document.getElementById('btn-move-fwd');
    const btnBwd = document.getElementById('btn-move-bwd');
    const inputDeg = document.getElementById('degrees');
    const btnSetZero = document.getElementById('btn-set-zero');
    const msg = document.getElementById('msg');
    // Config inputs
    const inpStepDeg = document.getElementById('step_degrees');
    const inpDwell = document.getElementById('dwell_ms');
    const inpInDelay = document.getElementById('slider_in_delay');
    const inpOutDelay = document.getElementById('slider_out_delay');
    const btnSaveCfg = document.getElementById('btn-save-config');
    const hall = document.getElementById('hall');
    const inductive = document.getElementById('inductive');
    const smin = document.getElementById('smin');
    const smax = document.getElementById('smax');

    function setBusy(b) {
        btnHome.disabled = b;
        btnFwd.disabled = b;
        btnBwd.disabled = b;
    }

    async function postJSON(url, body) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined
        });
        let data = null;
        try { data = await res.json(); } catch {}
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
        msg.textContent = 'Setting current position as zero...';
        setBusy(true);
        try {
            const data = await postJSON('/api/rotary/set_zero');
            msg.textContent = data.message || 'Zero set';
        } catch (e) {
            msg.textContent = 'Error: ' + e.message;
        } finally {
            setBusy(false);
        }
    });

    async function refreshStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            hall.classList.toggle('active', !!data.hall_status);
            inductive.classList.toggle('active', !!data.inductive_status);
            smin.classList.toggle('active', !!data.slider_min);
            smax.classList.toggle('active', !!data.slider_max);
            setBusy(!!data.is_running);
        } catch (e) {
            msg.textContent = 'Status error: ' + e.message;
        }
    }

    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            inpStepDeg.value = cfg.step_degrees;
            inpDwell.value = cfg.dwell_ms;
            inpInDelay.value = cfg.slider_in_delay;
            inpOutDelay.value = cfg.slider_out_delay;
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
                    dwell_ms: parseInt(inpDwell.value, 10),
                    slider_in_delay: parseFloat(inpInDelay.value),
                    slider_out_delay: parseFloat(inpOutDelay.value)
                })
            });
            const data = await res.json();
            if (!res.ok || data.success === false) throw new Error(data.message || res.statusText);
            msg.textContent = 'Configuration saved';
        } catch (e) {
            msg.textContent = 'Save config error: ' + e.message;
        }
    });

    refreshStatus();
    loadConfig();
    setInterval(refreshStatus, 1000);
});


