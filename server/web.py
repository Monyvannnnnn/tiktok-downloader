import json
import time
import asyncio
from config import PORT
from services.logger import recent_logs, log_activity

START_TIME = time.time()


async def handle_health_check(reader, writer):
    try:
        request_line = await reader.readline()
        while True:
            header_line = await reader.readline()
            if not header_line or header_line == b"\r\n":
                break

        req_str = request_line.decode("utf-8", errors="ignore")

        if "/api/logs" in req_str:
            body = json.dumps(list(recent_logs)).encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        elif "/api/stats" in req_str:
            logs_list = list(recent_logs)
            cache_hits = sum(1 for item in logs_list if "cache database" in item.get("text", "").lower())
            download_count = sum(1 for item in logs_list if "download" in item.get("text", "").lower())
            error_count = sum(1 for item in logs_list if "error" in item.get("text", "").lower())
            
            stats_data = {
                "uptime": int(time.time() - START_TIME),
                "total_logs": len(logs_list),
                "cache_hits": cache_hits,
                "download_requests": download_count,
                "errors": error_count,
                "status": "online"
            }
            body = json.dumps(stats_data).encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        else:
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrollSaver - TikTok Downloader Workflow & Terminal Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #080b11;
            --bg-card: rgba(22, 27, 34, 0.75);
            --border-glow: rgba(0, 242, 234, 0.25);
            --border-color: #21262d;
            --cyan-accent: #00f2fe;
            --pink-accent: #ff0050;
            --purple-accent: #7928ca;
            --green-success: #3fb950;
            --orange-warn: #d29922;
            --text-main: #f0f6fc;
            --text-muted: #8b949e;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 10% 20%, rgba(121, 40, 202, 0.15) 0px, transparent 50%),
                radial-gradient(at 90% 80%, rgba(0, 242, 254, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(255, 0, 80, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
        }

        .dashboard-container {
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Header Navigation */
        .navbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glow);
            padding: 18px 28px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--pink-accent), var(--cyan-accent));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: #fff;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
        }

        .brand-text h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 800;
            background: linear-gradient(90deg, #fff, var(--cyan-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .brand-text p {
            font-size: 12px;
            color: var(--text-muted);
        }

        .nav-status {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(63, 185, 80, 0.12);
            color: var(--green-success);
            border: 1px solid rgba(63, 185, 80, 0.3);
            padding: 8px 16px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--green-success);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--green-success);
            animation: pulse-glow 2s infinite;
        }

        @keyframes pulse-glow {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Metrics Bar */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }

        .metric-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            border-color: var(--cyan-accent);
        }

        .metric-info h3 {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 6px;
        }

        .metric-value {
            font-family: 'Outfit', sans-serif;
            font-size: 26px;
            font-weight: 700;
            color: #fff;
        }

        .metric-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--cyan-accent);
        }

        /* Workflow Visual Section */
        .section-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }

        .section-header {
            padding: 20px 26px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .section-title {
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title i {
            color: var(--cyan-accent);
        }

        /* Workflow Pipeline Flowchart */
        .workflow-pipeline {
            padding: 36px 26px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            position: relative;
        }

        .wf-step {
            position: relative;
            background: rgba(13, 17, 23, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 22px 18px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            transition: all 0.3s ease;
        }

        .wf-step:hover {
            border-color: var(--cyan-accent);
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.15);
            transform: translateY(-4px);
        }

        .wf-step-number {
            position: absolute;
            top: -12px;
            background: linear-gradient(135deg, var(--cyan-accent), var(--purple-accent));
            color: #fff;
            font-size: 11px;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 12px;
        }

        .wf-icon-box {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            color: var(--cyan-accent);
            margin: 10px 0 14px 0;
            transition: all 0.3s ease;
        }

        .wf-step:hover .wf-icon-box {
            background: var(--cyan-accent);
            color: #000;
            box-shadow: 0 0 20px var(--cyan-accent);
        }

        .wf-title {
            font-family: 'Outfit', sans-serif;
            font-size: 15px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 6px;
        }

        .wf-desc {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        /* Live Terminal Logs */
        .terminal-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .search-box {
            background: rgba(0,0,0,0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 6px 12px;
            color: #fff;
            font-size: 13px;
            outline: none;
            width: 220px;
            transition: border-color 0.2s;
        }

        .search-box:focus {
            border-color: var(--cyan-accent);
        }

        .btn-action {
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }

        .btn-action:hover {
            background: rgba(255,255,255,0.12);
            color: #fff;
        }

        .terminal-window {
            height: 480px;
            overflow-y: auto;
            background: #06090e;
            font-family: 'Fira Code', monospace;
            font-size: 13px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .log-row {
            display: flex;
            gap: 14px;
            padding: 6px 10px;
            border-radius: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
            line-height: 1.5;
            word-break: break-all;
        }

        .log-row:hover {
            background: rgba(255, 255, 255, 0.04);
        }

        .log-ts {
            color: var(--text-muted);
            flex-shrink: 0;
            font-size: 12px;
        }

        .log-msg {
            color: #e6edf3;
        }

        .log-msg.highlight-cache {
            color: #3fb950;
            font-weight: 500;
        }

        .log-msg.highlight-error {
            color: #ff7b72;
            font-weight: 500;
        }

        .log-msg.highlight-download {
            color: var(--cyan-accent);
        }

        .empty-logs {
            text-align: center;
            padding: 60px;
            color: var(--text-muted);
            font-size: 14px;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 16px;
            font-size: 13px;
            color: var(--text-muted);
        }

        .footer a {
            color: var(--cyan-accent);
            text-decoration: none;
        }

        @media (max-width: 768px) {
            .navbar { flex-direction: column; align-items: flex-start; gap: 14px; }
            .terminal-controls { width: 100%; flex-wrap: wrap; }
            .search-box { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Navbar -->
        <nav class="navbar">
            <div class="brand">
                <div class="brand-icon">
                    <i class="fa-brands fa-tiktok"></i>
                </div>
                <div class="brand-text">
                    <h1>ScrollSaver Dashboard</h1>
                    <p>High-Performance Telegram TikTok Downloader Bot</p>
                </div>
            </div>
            <div class="nav-status">
                <div class="status-pill">
                    <span class="status-dot"></span>
                    <span>Bot System Active</span>
                </div>
            </div>
        </nav>

        <!-- Live Metrics Cards -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-info">
                    <h3>System Uptime</h3>
                    <div class="metric-value" id="stat-uptime">0s</div>
                </div>
                <div class="metric-icon" style="color: var(--cyan-accent);">
                    <i class="fa-solid fa-clock"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Total Requests</h3>
                    <div class="metric-value" id="stat-logs">0</div>
                </div>
                <div class="metric-icon" style="color: var(--purple-accent);">
                    <i class="fa-solid fa-bolt"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Cache Hits</h3>
                    <div class="metric-value" id="stat-cache">0</div>
                </div>
                <div class="metric-icon" style="color: var(--green-success);">
                    <i class="fa-solid fa-database"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Active Services</h3>
                    <div class="metric-value">4 / 4</div>
                </div>
                <div class="metric-icon" style="color: var(--orange-warn);">
                    <i class="fa-solid fa-server"></i>
                </div>
            </div>
        </div>

        <!-- Workflow Visual Architecture -->
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">
                    <i class="fa-solid fa-diagram-project"></i>
                    <span>System Workflow Architecture</span>
                </div>
            </div>
            <div class="workflow-pipeline">
                <div class="wf-step">
                    <span class="wf-step-number">STEP 01</span>
                    <div class="wf-icon-box">
                        <i class="fa-paper-plane"></i>
                    </div>
                    <div class="wf-title">User Telegram Link</div>
                    <div class="wf-desc">User sends TikTok video or photo link to @thescrollsaver_bot</div>
                </div>

                <div class="wf-step">
                    <span class="wf-step-number">STEP 02</span>
                    <div class="wf-icon-box">
                        <i class="fa-magnifying-glass"></i>
                    </div>
                    <div class="wf-title">Detail Extractor</div>
                    <div class="wf-desc">Fast metadata lookup via TikWM API or direct TikTok rehydration scraping</div>
                </div>

                <div class="wf-step">
                    <span class="wf-step-number">STEP 03</span>
                    <div class="wf-icon-box">
                        <i class="fa-database"></i>
                    </div>
                    <div class="wf-title">Database Cache</div>
                    <div class="wf-desc">Check cached Telegram file_id in SQLite/MySQL for instant 0-second re-send</div>
                </div>

                <div class="wf-step">
                    <span class="wf-step-number">STEP 04</span>
                    <div class="wf-icon-box">
                        <i class="fa-download"></i>
                    </div>
                    <div class="wf-title">Downloader Engine</div>
                    <div class="wf-desc">Fetch no-watermark HD video stream, fallback to Musicaldown, or batch slideshow photos</div>
                </div>

                <div class="wf-step">
                    <span class="wf-step-number">STEP 05</span>
                    <div class="wf-icon-box">
                        <i class="fa-share-from-square"></i>
                    </div>
                    <div class="wf-title">Telegram Dispatch</div>
                    <div class="wf-desc">Send HD video / media group album to user with inline source video button</div>
                </div>
            </div>
        </div>

        <!-- Terminal Log Monitor -->
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">
                    <i class="fa-solid fa-terminal"></i>
                    <span>Live Activity Stream</span>
                </div>
                <div class="terminal-controls">
                    <input type="text" id="search-input" class="search-box" placeholder="Search activity logs...">
                    <button class="btn-action" onclick="fetchData()"><i class="fa-solid fa-rotate-right"></i> Refresh</button>
                    <button class="btn-action" onclick="toggleAutoScroll()"><i class="fa-solid fa-lock" id="lock-icon"></i> Auto-Scroll: ON</button>
                </div>
            </div>
            <div class="terminal-window" id="terminal-body">
                <div class="empty-logs">Connecting to live log stream...</div>
            </div>
        </div>

        <div class="footer">
            Powered by <strong>@thescrollsaver_bot</strong> &bull; ScrollSaver Automation Server
        </div>
    </div>

    <script>
        let autoScroll = true;
        let searchQuery = "";

        document.getElementById('search-input').addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase();
            renderLogs();
        });

        let cachedLogs = [];

        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            if (h > 0) return `${h}h ${m}m ${s}s`;
            if (m > 0) return `${m}m ${s}s`;
            return `${s}s`;
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                document.getElementById('stat-uptime').innerText = formatUptime(stats.uptime || 0);
                document.getElementById('stat-logs').innerText = stats.total_logs || 0;
                document.getElementById('stat-cache').innerText = stats.cache_hits || 0;
            } catch (err) {
                console.error("Stats fetch error:", err);
            }
        }

        async function fetchData() {
            try {
                const res = await fetch('/api/logs');
                cachedLogs = await res.json();
                renderLogs();
                fetchStats();
            } catch (err) {
                console.error("Logs fetch error:", err);
            }
        }

        function renderLogs() {
            const container = document.getElementById('terminal-body');
            if (!cachedLogs || cachedLogs.length === 0) {
                container.innerHTML = '<div class="empty-logs">No activity logged yet. Send a TikTok link in Telegram to start!</div>';
                return;
            }

            const filtered = cachedLogs.filter(item => {
                if (!searchQuery) return true;
                return item.text.toLowerCase().includes(searchQuery) || item.time.toLowerCase().includes(searchQuery);
            });

            if (filtered.length === 0) {
                container.innerHTML = '<div class="empty-logs">No matching activity logs found for your search filter.</div>';
                return;
            }

            container.innerHTML = filtered.map(item => {
                let text = escapeHtml(item.text);
                let extraClass = "";
                if (text.toLowerCase().includes("cache database")) extraClass = "highlight-cache";
                else if (text.toLowerCase().includes("error") || text.toLowerCase().includes("failed")) extraClass = "highlight-error";
                else if (text.toLowerCase().includes("download") || text.toLowerCase().includes("video id")) extraClass = "highlight-download";

                return `
                    <div class="log-row">
                        <span class="log-ts">[${item.time} UTC]</span>
                        <span class="log-msg ${extraClass}">${text}</span>
                    </div>
                `;
            }).join('');

            if (autoScroll) {
                container.scrollTop = 0;
            }
        }

        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            const btn = document.getElementById('lock-icon');
            const btnParent = btn.parentElement;
            if (autoScroll) {
                btn.className = "fa-solid fa-lock";
                btnParent.innerHTML = '<i class="fa-solid fa-lock" id="lock-icon"></i> Auto-Scroll: ON';
            } else {
                btn.className = "fa-solid fa-lock-open";
                btnParent.innerHTML = '<i class="fa-solid fa-lock-open" id="lock-icon"></i> Auto-Scroll: OFF';
            }
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        fetchData();
        setInterval(fetchData, 2000);
    </script>
</body>
</html>"""
            body = html_content.encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
        await writer.drain()
    except Exception as e:
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_web_server():
    try:
        await asyncio.start_server(handle_health_check, "0.0.0.0", PORT)
        log_activity(f"HTTP health server started on port {PORT}")
    except Exception as e:
        log_activity(f"Port binding note: {e}")
