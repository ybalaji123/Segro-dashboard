/**
 * Smart Segro Dashboard — Frontend Logic
 * ───────────────────────────────────────
 * Polls GET /api/dashboard-data every 2 seconds.
 * Updates 3 stat cards + recent activity table.
 * Sets system status indicator based on data freshness.
 */

// When served from FastAPI, use relative URLs.
// When opening index.html directly, override this with your laptop's IP.
const API_BASE = "";

// ── DOM Refs ────────────────────────────────────────────────────────────────
const totalEl    = document.getElementById("total-count");
const metalsEl   = document.getElementById("metals-count");
const plasticsEl = document.getElementById("plastics-count");
const bodyEl     = document.getElementById("activity-body");
const dotEl      = document.getElementById("status-dot");
const labelEl    = document.getElementById("status-label");

// Cache previous counts for count-up flash detection
let prevCounts = { total: null, metals: null, plastics: null };

// Track consecutive errors for backoff
let errorStreak = 0;

// ── Helpers ─────────────────────────────────────────────────────────────────

/** Format an ISO timestamp string to "HH:MM:SS AM/PM" */
function formatTime(isoStr) {
    try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString([], {
            hour: "2-digit", minute: "2-digit", second: "2-digit",
        });
    } catch {
        return isoStr;
    }
}

/** Format an ISO timestamp string to "Apr 12, 10:45:22 AM" */
function formatDateTime(isoStr) {
    try {
        const d = new Date(isoStr);
        return d.toLocaleString([], {
            month:  "short",
            day:    "numeric",
            hour:   "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    } catch {
        return isoStr;
    }
}

/** Animated number count-up from old value to new */
function animateCount(el, newVal) {
    const oldVal = parseInt(el.textContent) || 0;
    if (oldVal === newVal) return;

    // Flash accent colour on change
    el.classList.remove("flash");
    void el.offsetWidth;          // force reflow
    el.classList.add("flash");

    const duration = 600;         // ms
    const start    = performance.now();

    function step(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased    = 1 - Math.pow(1 - progress, 3);   // ease-out cubic
        el.textContent = Math.round(oldVal + (newVal - oldVal) * eased);
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

/** Return styled HTML for a material tag (Metal vs Plastic) */
function materialTag(wasteType) {
    const isMetal = /metal/i.test(wasteType);
    const cls  = isMetal ? "tag-metal"  : "tag-plastic";
    const icon = isMetal ? "⚙"         : "♻";
    return `<span class="material-tag ${cls}">${icon} ${wasteType}</span>`;
}

/** Return styled HTML for a status badge */
function statusTag(statusStr) {
    return `<span class="status-tag">✔ ${statusStr}</span>`;
}

// ── System Status Indicator ─────────────────────────────────────────────────

/**
 * Update the header status pill.
 * - Green "System Online"  → data arrived within the last 10 s
 * - Yellow "Sorting…"      → data between 10 s and 60 s old
 * - Red "Check Bin"        → data older than 60 s or fetch error
 */
function updateStatusIndicator(latestTimestamp, hasError) {
    dotEl.className = "status-dot";   // reset

    if (hasError) {
        dotEl.classList.add("error");
        labelEl.textContent = "Error / Check Bin";
        return;
    }

    if (!latestTimestamp) {
        labelEl.textContent = "Waiting for ESP32…";
        return;
    }

    const ageSec = (Date.now() - new Date(latestTimestamp).getTime()) / 1000;

    if (ageSec < 10) {
        dotEl.classList.add("online");
        labelEl.textContent = "System Online";
    } else if (ageSec < 60) {
        dotEl.classList.add("sorting");
        labelEl.textContent = "Sorting…";
    } else {
        dotEl.classList.add("error");
        labelEl.textContent = "Check Bin";
    }
}

// ── Activity Table ──────────────────────────────────────────────────────────

/** Rebuild the activity table with the latest entries */
function renderActivity(entries) {
    if (!entries || entries.length === 0) {
        bodyEl.innerHTML = `
            <tr class="placeholder-row">
                <td colspan="3">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="1.5" aria-hidden="true">
                            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                            <polyline points="13 2 13 9 20 9"/>
                        </svg>
                        <p>No activity recorded yet. Drop some waste!</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    bodyEl.innerHTML = entries
        .map((e, i) => `
            <tr style="animation-delay:${i * 60}ms">
                <td class="cell-time">${formatDateTime(e.timestamp)}</td>
                <td>${materialTag(e.waste_type)}</td>
                <td>${statusTag(e.status)}</td>
            </tr>`)
        .join("");
}

// ── Main Poll Function ──────────────────────────────────────────────────────

async function fetchDashboardData() {
    try {
        const res = await fetch(`${API_BASE}/api/dashboard-data`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        errorStreak = 0;

        // Update metric cards with count-up animation
        animateCount(totalEl,    data.total_processed ?? 0);
        animateCount(metalsEl,   data.metals_count    ?? 0);
        animateCount(plasticsEl, data.plastics_count  ?? 0);

        // Render activity table
        renderActivity(data.recent_activity || []);

        // Update status from most recent entry's timestamp
        const latestTs = data.recent_activity?.[0]?.timestamp ?? null;
        updateStatusIndicator(latestTs, false);

    } catch (err) {
        errorStreak++;
        console.warn(`[Segro] Fetch error (streak ${errorStreak}):`, err.message);
        updateStatusIndicator(null, true);
    }
}

// ── Bootstrap ───────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    // Immediate first load, then poll every 2 seconds
    fetchDashboardData();
    setInterval(fetchDashboardData, 2000);
});
