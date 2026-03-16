const API_BASE = "http://localhost:8000/api";

// DOM Elements
const bins = {
    "Metal": document.getElementById('metal-bin'),
    "Plastic": document.getElementById('plastic-bin'),
    "Other": document.getElementById('normal-bin')
};

const feedContainer = document.getElementById('sensor-feed');
let historyChart = null;

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('historyChart').getContext('2d');
    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Fill Level (%)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Update the visual of a specific bin
function updateBinUI(category, percentage) {
    const binEl = bins[category] || bins["Other"];
    const fillEl = binEl.querySelector('.fill-level');
    const percentEl = binEl.querySelector('.percentage-display');
    const statusText = binEl.querySelector('.status-text');

    fillEl.style.height = `${percentage}%`;
    percentEl.textContent = `${Math.round(percentage)}%`;

    if (percentage > 90) {
        statusText.textContent = "Full";
        statusText.className = "status-text full";
    } else if (percentage > 70) {
        statusText.textContent = "Warning";
        statusText.className = "status-text warning";
    } else {
        statusText.textContent = "Normal";
        statusText.className = "status-text ok";
    }
}

// Add an item to the feed
function addToFeed(item) {
    const time = new Date(item.timestamp).toLocaleTimeString();
    const itemEl = document.createElement('div');
    itemEl.className = 'feed-item';
    
    // Clear placeholder if it exists
    const placeholder = feedContainer.querySelector('.placeholder');
    if (placeholder) placeholder.remove();

    const catClass = `cat-${item.waste_category.toLowerCase()}`;
    
    itemEl.innerHTML = `
        <div class="item-info">
            <span class="item-cat ${catClass}">${item.waste_category}</span>
            <span class="item-time" style="margin-left: 10px; font-size: 0.8rem; color: #94a3b8;">${time}</span>
        </div>
        <div class="item-meta" style="font-size: 0.9rem;">
            Dist: ${item.ultrasonic_distance}cm
        </div>
    `;

    feedContainer.prepend(itemEl);

    // Keep only last 10
    if (feedContainer.children.length > 10) {
        feedContainer.removeChild(feedContainer.lastChild);
    }
}

// Fetch latest data from API
async function fetchLatest() {
    try {
        const response = await fetch(`${API_BASE}/latest`);
        const data = await response.json();
        
        const statusBadge = document.getElementById('system-status');
        const pulse = document.querySelector('.pulse');

        if (data && data.waste_category && data.timestamp) {
            // Check if data is "fresh" (sent within last 10 seconds)
            const lastSeen = new Date(data.timestamp);
            const now = new Date();
            const diffSeconds = (now - lastSeen) / 1000;

            if (diffSeconds < 10) {
                statusBadge.textContent = "ESP32 Online";
                pulse.style.backgroundColor = "var(--accent-normal)";
                pulse.style.boxShadow = "0 0 10px var(--accent-normal)";
            } else {
                statusBadge.textContent = "ESP32 Standby";
                pulse.style.backgroundColor = "var(--accent-warning)";
                pulse.style.boxShadow = "0 0 10px var(--accent-warning)";
            }

            updateBinUI(data.waste_category, data.fill_percentage || 0);
            
            // Only add to feed if it's a new entry (simplification for this demo)
            // In a real app we'd compare IDs
            const latestFeedItem = feedContainer.querySelector('.feed-item:not(.placeholder) .item-time');
            const dataTime = new Date(data.timestamp).toLocaleTimeString();
            if (!latestFeedItem || latestFeedItem.textContent !== dataTime) {
                addToFeed(data);
                
                // Update chart with live point
                if (historyChart) {
                    const label = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    historyChart.data.labels.push(label);
                    historyChart.data.datasets[0].data.push(data.fill_percentage);
                    if (historyChart.data.labels.length > 20) {
                        historyChart.data.labels.shift();
                        historyChart.data.datasets[0].data.shift();
                    }
                    historyChart.update('none');
                }
            }
        } else {
            statusBadge.textContent = "Waiting for ESP32...";
            pulse.style.backgroundColor = "#94a3b8";
        }
    } catch (error) {
        console.error("Error fetching latest data:", error);
    }
}

// Fetch history initially
async function fetchHistory() {
    try {
        const response = await fetch(`${API_BASE}/history?limit=10`);
        const data = await response.json();
        
        if (Array.isArray(data)) {
            data.reverse().forEach(item => {
                const time = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                historyChart.data.labels.push(time);
                historyChart.data.datasets[0].data.push(item.fill_percentage);
                addToFeed(item);
            });
            historyChart.update();
        }
    } catch (error) {
        console.error("Error fetching history:", error);
    }
}

// Initial Run
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchHistory();
    // Poll every 3 seconds
    setInterval(fetchLatest, 3000);
});
