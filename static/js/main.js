document.addEventListener('DOMContentLoaded', () => {

    // --- Theme Toggle ---
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const icon = themeToggle.querySelector('ion-icon');

    // Check saved theme
    if (localStorage.getItem('theme') === 'light') {
        body.classList.add('light-mode');
        icon.setAttribute('name', 'sunny-outline');
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('light-mode');
        const isLight = body.classList.contains('light-mode');
        icon.setAttribute('name', isLight ? 'sunny-outline' : 'moon-outline');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });

    // --- History Logic ---
    const historyToggle = document.getElementById('history-toggle');
    const historyClose = document.getElementById('history-close');
    const historyDrawer = document.getElementById('history-drawer');
    const historyOverlay = document.getElementById('history-overlay');
    const historyList = document.getElementById('history-list');

    function toggleHistory(show) {
        if (show) {
            historyDrawer.classList.add('active');
            historyOverlay.classList.remove('hidden');
            setTimeout(() => historyOverlay.classList.add('active'), 10);
            fetchHistory();
        } else {
            historyDrawer.classList.remove('active');
            historyOverlay.classList.remove('active');
            setTimeout(() => historyOverlay.classList.add('hidden'), 300);
        }
    }

    historyToggle.addEventListener('click', () => toggleHistory(true));
    historyClose.addEventListener('click', () => toggleHistory(false));
    historyOverlay.addEventListener('click', () => toggleHistory(false));

    async function fetchHistory() {
        try {
            const res = await fetch('/history');
            const data = await res.json();
            renderHistory(data);
        } catch (e) {
            console.error("Failed to load history", e);
        }
    }

    function renderHistory(items) {
        historyList.innerHTML = '';
        if (items.length === 0) {
            historyList.innerHTML = '<div class="empty-state">No downloads yet</div>';
            return;
        }

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';

            // Format format label
            let fmtLabel = item.format;
            if (fmtLabel.startsWith('video_')) fmtLabel = fmtLabel.replace('video_', 'Video ');
            if (fmtLabel.startsWith('audio_')) fmtLabel = fmtLabel.replace('audio_', 'Audio ');

            div.innerHTML = `
                <div class="history-title" title="${item.title}">${item.title}</div>
                <div class="history-meta">
                    <span class="history-tag">${fmtLabel}</span>
                    <span>${item.date}</span>
                </div>
            `;
            // Click to download again (serve file)
            div.addEventListener('click', () => {
                window.location.href = `/downloads/${encodeURIComponent(item.filename)}`;
            });
            div.style.cursor = 'pointer';

            historyList.appendChild(div);
        });
    }

    // --- Download Logic ---
    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url');
    const btn = document.getElementById('download-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');

    const statusText = document.getElementById('status-text');
    const percentText = document.getElementById('percent-text');
    const speedText = document.getElementById('speed-text');
    const etaText = document.getElementById('eta-text');
    const sizeText = document.getElementById('size-text');
    const errorBox = document.getElementById('error-message');

    let eventSource = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Reset UI
        errorBox.classList.add('hidden');
        document.getElementById('success-action').classList.add('hidden');
        progressContainer.classList.remove('hidden');
        btn.disabled = true;
        progressBar.style.width = '0%';
        percentText.textContent = '0%';
        statusText.textContent = 'Initializing...';
        speedText.textContent = '--/s';
        etaText.textContent = '--:--';
        sizeText.textContent = '-- MB';

        const url = urlInput.value;
        const format = document.getElementById('format-select').value; // Changed to select

        try {
            // 1. Start Download
            const response = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, format })
            });

            // Check for JSON response
            const contentType = response.headers.get("content-type");
            let result;

            if (contentType && contentType.indexOf("application/json") !== -1) {
                result = await response.json();
            } else {
                // Backend crashed or returned HTML
                const text = await response.text();
                console.error("Server returned non-JSON:", text);
                throw new Error(`Server Error (${response.status}): The server crashed or returned an invalid response.`);
            }

            if (response.status !== 200) {
                throw new Error(result.message || 'Failed to start download');
            }

            // 2. Connect to SSE
            if (eventSource) eventSource.close();

            eventSource = new EventSource('/progress');

            eventSource.onmessage = (e) => {
                const data = JSON.parse(e.data);

                if (data.keep_alive) return;

                if (data.status === 'downloading') {
                    const pct = data.percentage;
                    progressBar.style.width = pct + '%';
                    percentText.textContent = data.percentage_str;
                    statusText.textContent = 'Downloading...';
                    speedText.textContent = data.speed;
                    etaText.textContent = data.eta;

                    if (data.total) {
                        sizeText.textContent = data.total; // already formatted
                    }

                } else if (data.status === 'processing') {
                    statusText.textContent = data.message;
                    progressBar.style.width = '100%';
                    percentText.textContent = '100%';
                    etaText.textContent = 'Done';

                } else if (data.status === 'finished') {
                    statusText.textContent = 'Server Download Complete!';
                    statusText.style.color = 'var(--accent-color)';
                    progressBar.style.width = '100%';
                    btn.disabled = false;

                    // Show Save Button
                    const successAction = document.getElementById('success-action');
                    const saveBtn = document.getElementById('save-file-btn');
                    successAction.classList.remove('hidden');
                    saveBtn.href = `/downloads/${encodeURIComponent(data.filename)}`;

                    // Optional: Auto-trigger download
                    // window.location.href = saveBtn.href;

                    fetchHistory(); // Refresh history list
                    eventSource.close();

                } else if (data.status === 'error') {
                    throw new Error(data.message);
                }
            };

            eventSource.onerror = () => {
                // If connection drops but we aren't finished, it might be a network error
                // For now, we rely on the 'finished' message to close.
                // console.log("SSE Connection closed or error");
            };

        } catch (err) {
            console.error(err);
            errorBox.textContent = err.message;
            errorBox.classList.remove('hidden');
            progressContainer.classList.add('hidden');
            btn.disabled = false;
            if (eventSource) eventSource.close();
        }
    });
});
