document.addEventListener('DOMContentLoaded', () => {
    const btnHome = document.getElementById('btn-home');
    const btnFwd = document.getElementById('btn-move-fwd');
    const btnBwd = document.getElementById('btn-move-bwd');
    const inputDeg = document.getElementById('degrees');
    const msg = document.getElementById('msg');
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

    refreshStatus();
    setInterval(refreshStatus, 1000);
});


