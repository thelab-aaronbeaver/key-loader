// In file: static/script.js

document.addEventListener('DOMContentLoaded', function () {
    const startButton = document.getElementById('start-button');
    const homeButton = document.getElementById('home-button'); // Added
    const angleDisplay = document.getElementById('current-angle');
    const messageDisplay = document.getElementById('system-message');
    const homedDisplay = document.getElementById('homed-status'); // Added
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
        messageDisplay.textContent = 'Starting cycle...';
        const cyclesInput = document.getElementById('cycles');
        const cycles = cyclesInput ? parseInt(cyclesInput.value, 10) || 1 : 1;
        try {
            await fetch('/api/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cycles }) });
        } catch (e) {
            // no-op; errors reflected via /api/status polling
        }
    });

    function updateStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                angleDisplay.textContent = data.current_angle + '°';
                messageDisplay.textContent = data.system_message;

                // --- MODIFIED: Update homing status display ---
                if (data.is_homed) {
                    homedDisplay.textContent = 'Homed';
                    homedDisplay.className = 'status-value homed-yes';
                } else {
                    homedDisplay.textContent = 'Not Homed';
                    homedDisplay.className = 'status-value homed-no';
                }

                hallIndicator.classList.toggle('active', data.hall_status);
                inductiveIndicator.classList.toggle('active', data.inductive_status);
                sliderMinIndicator.classList.toggle('active', data.slider_min);
                sliderMaxIndicator.classList.toggle('active', data.slider_max);

                // --- ADDED: Update cycle progress display ---
                if (data.total_cycles > 0) {
                    cyclesProgressDisplay.textContent = `${data.current_cycle} of ${data.total_cycles}`;
                    currentPositionDisplay.textContent = `Position ${data.current_cycle}`;
                } else {
                    cyclesProgressDisplay.textContent = '0 of 0';
                    currentPositionDisplay.textContent = 'Position 0';
                }

                // --- MODIFIED: Disable/Enable buttons logically ---
                const isBusy = data.is_running;
                homeButton.disabled = isBusy;
                // Start button is disabled if busy OR if not homed
                startButton.disabled = isBusy || !data.is_homed;
            });
    }

    setInterval(updateStatus, 1000);
});