// In file: static/script.js

document.addEventListener('DOMContentLoaded', function () {
    const startButton = document.getElementById('start-button');
    const homeButton = document.getElementById('home-button'); // Added
    const angleDisplay = document.getElementById('current-angle');
    const messageDisplay = document.getElementById('system-message');
    const homedDisplay = document.getElementById('homed-status'); // Added
    const hallIndicator = document.getElementById('hall-status');
    const inductiveIndicator = document.getElementById('inductive-status');

    // --- ADDED: Event listener for the Home button ---
    homeButton.addEventListener('click', () => {
        messageDisplay.textContent = 'Homing sequence initiated...';
        fetch('/api/home', { method: 'POST' });
    });

    startButton.addEventListener('click', () => {
        messageDisplay.textContent = 'Starting cycle...';
        fetch('/api/start', { method: 'POST' });
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

                // --- MODIFIED: Disable/Enable buttons logically ---
                const isBusy = data.is_running;
                homeButton.disabled = isBusy;
                // Start button is disabled if busy OR if not homed
                startButton.disabled = isBusy || !data.is_homed;
            });
    }

    setInterval(updateStatus, 1000);
});