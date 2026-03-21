// PhotographyHub WebSocket Client
(function () {
    'use strict';

    let socket = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 3000;

    function getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/notifications/`;
    }

    function showToast(message, type = 'info', duration = 6000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const colors = {
            info: 'bg-blue-600',
            success: 'bg-green-600',
            warning: 'bg-yellow-500',
            new_job: 'bg-teal-700 border-l-4 border-yellow-400',
        };
        const colorClass = colors[type] || colors.info;

        toast.className = `toast-enter ${colorClass} text-white p-4 rounded-lg shadow-xl mb-3 max-w-sm cursor-pointer`;
        toast.innerHTML = `
            <div class="flex items-start gap-3">
                <span class="text-2xl">${type === 'new_job' ? '📸' : 'ℹ️'}</span>
                <div class="flex-1">
                    <p class="font-semibold text-sm">New Job Available!</p>
                    <p class="text-xs mt-1 opacity-90">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-white opacity-70 hover:opacity-100 text-lg leading-none">&times;</button>
            </div>
        `;
        toast.addEventListener('click', function (e) {
            if (e.target.tagName !== 'BUTTON') {
                window.location.href = '/bookings/job-feed/';
            }
        });

        container.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }

    function handleMessage(data) {
        if (data.type === 'connection_established') {
            console.log('✅ PhotographyHub: WebSocket connected');
            return;
        }

        if (data.type === 'new_booking_ping') {
            const budget = data.budget ? `₹${data.budget}` : 'Open';
            const msg = `${data.service_name} • ${data.customer_address} • ${data.distance_km} km away • Budget: ${budget}`;
            showToast(msg, 'new_job');

            // Refresh job feed if we're on that page
            const jobFeedContainer = document.getElementById('job-feed-container');
            if (jobFeedContainer) {
                // Add new job card dynamically
                const event = new CustomEvent('newJobPing', { detail: data });
                document.dispatchEvent(event);
            }
        }
    }

    function connect() {
        if (!document.body.dataset.userId) return; // Not logged in

        try {
            socket = new WebSocket(getWebSocketURL());

            socket.onopen = function () {
                reconnectAttempts = 0;
                console.log('🔗 WebSocket connection established');
            };

            socket.onmessage = function (event) {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            socket.onerror = function (error) {
                console.error('WebSocket error:', error);
            };

            socket.onclose = function (event) {
                console.log('WebSocket closed:', event.code);
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttempts++;
                    console.log(`Reconnecting in ${RECONNECT_DELAY}ms... (attempt ${reconnectAttempts})`);
                    setTimeout(connect, RECONNECT_DELAY);
                }
            };
        } catch (e) {
            console.error('Failed to create WebSocket:', e);
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connect);
    } else {
        connect();
    }

    // Expose for external use
    window.PhotographyHub = { showToast };
})();
