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
    <title>ScrollSaver - White Isometric Process Map & Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --border-color: #e2e8f0;
            --pink-path: #e11d48;
            --green-path: #10b981;
            --purple-path: #6366f1;
            --cyan-path: #0284c7;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --shadow-subtle: 0 10px 30px rgba(0, 0, 0, 0.05);
            --shadow-card: 0 14px 35px rgba(15, 23, 42, 0.08);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(at 10% 10%, rgba(99, 102, 241, 0.05) 0px, transparent 40%),
                radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.05) 0px, transparent 40%),
                radial-gradient(at 50% 50%, rgba(225, 29, 72, 0.04) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
        }

        .dashboard-container {
            max-width: 1440px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Top Bar */
        .navbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 16px 28px;
            border-radius: 20px;
            box-shadow: var(--shadow-card);
        }

        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon {
            width: 44px; height: 44px; border-radius: 12px;
            background: linear-gradient(135deg, var(--pink-path), var(--purple-path));
            display: flex; align-items: center; justify-content: center;
            font-size: 22px; color: #fff; box-shadow: 0 4px 14px rgba(225, 29, 72, 0.3);
        }

        .brand-text h1 {
            font-family: 'Outfit', sans-serif; font-size: 22px; font-weight: 800;
            color: var(--text-main); letter-spacing: -0.5px;
        }

        .brand-text p { font-size: 12px; color: var(--text-muted); }

        .nav-controls { display: flex; align-items: center; gap: 16px; }

        .view-btn {
            background: #f1f5f9; border: 1px solid var(--border-color);
            color: var(--text-main); padding: 8px 16px; border-radius: 10px;
            font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px;
            transition: all 0.2s ease;
        }

        .view-btn.active, .view-btn:hover {
            background: var(--cyan-path); border-color: var(--cyan-path); color: #ffffff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        }

        /* Metrics Bar */
        .metrics-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;
        }

        .metric-card {
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 16px; padding: 18px 22px; display: flex; align-items: center; justify-content: space-between;
            box-shadow: var(--shadow-subtle); transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px); box-shadow: var(--shadow-card);
        }

        .metric-info h3 { font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 800; color: var(--text-main); }
        .metric-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; background: #f8fafc; border: 1px solid var(--border-color); }

        /* Main Workspace Container */
        .main-section {
            background: var(--bg-card); border: 1px solid var(--border-color);
            border-radius: 24px; padding: 24px; position: relative; overflow: hidden;
            box-shadow: var(--shadow-card);
        }

        .section-header {
            display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
            padding-bottom: 16px; border-bottom: 1px solid var(--border-color);
        }

        .section-title {
            font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 800; color: var(--text-main);
            display: flex; align-items: center; gap: 10px;
        }

        /* Legend Bar */
        .legend-bar {
            display: flex; align-items: center; gap: 20px; flex-wrap: wrap; font-size: 13px; font-weight: 600; color: var(--text-muted);
        }

        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .dot-pink { background: var(--pink-path); box-shadow: 0 0 8px rgba(225, 29, 72, 0.4); }
        .dot-green { background: var(--green-path); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
        .dot-purple { background: var(--purple-path); box-shadow: 0 0 8px rgba(99, 102, 241, 0.4); }

        /* ISOMETRIC CANVAS CONTAINER - WHITE THEME */
        .iso-map-wrapper {
            width: 100%; height: 680px; position: relative; border-radius: 16px;
            background: radial-gradient(circle at center, #ffffff, #f1f5f9);
            border: 1px solid var(--border-color); overflow: hidden; display: flex; align-items: center; justify-content: center;
            box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.02);
        }

        .iso-map-viewport {
            width: 1100px; height: 600px; position: relative;
            transform: rotateX(24deg) rotateZ(-12deg);
            transform-style: preserve-3d; transition: transform 0.5s ease;
        }

        .iso-map-wrapper:hover .iso-map-viewport {
            transform: rotateX(18deg) rotateZ(-8deg);
        }

        /* SVG Paths */
        .svg-canvas {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;
        }

        .path-pink { stroke: var(--pink-path); stroke-width: 4; fill: none; stroke-linecap: round; filter: drop-shadow(0 2px 4px rgba(225, 29, 72, 0.3)); }
        .path-green { stroke: var(--green-path); stroke-width: 4; fill: none; stroke-linecap: round; filter: drop-shadow(0 2px 4px rgba(16, 185, 129, 0.3)); }
        .path-purple { stroke: var(--purple-path); stroke-width: 4; fill: none; stroke-linecap: round; filter: drop-shadow(0 2px 4px rgba(99, 102, 241, 0.3)); }

        .animated-dash {
            stroke-dasharray: 12 12; animation: flow-dash 1.5s linear infinite;
        }

        @keyframes flow-dash {
            from { stroke-dashoffset: 48; }
            to { stroke-dashoffset: 0; }
        }

        /* Isometric Nodes - Clean White Cards */
        .iso-node {
            position: absolute; width: 155px; padding: 14px; border-radius: 16px;
            background: #ffffff; border: 1px solid #e2e8f0;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.1); cursor: pointer; transition: all 0.3s ease;
            display: flex; flex-direction: column; align-items: center; text-align: center;
        }

        .iso-node:hover {
            transform: translateZ(24deg) scale(1.08); border-color: var(--cyan-path);
            box-shadow: 0 20px 40px rgba(2, 132, 199, 0.2); z-index: 50;
        }

        .node-badge {
            width: 26px; height: 26px; border-radius: 50%; font-size: 11px; font-weight: 800;
            display: flex; align-items: center; justify-content: center; color: #ffffff; margin-bottom: 8px;
            box-shadow: 0 3px 8px rgba(0,0,0,0.15);
        }

        .badge-pink { background: var(--pink-path); }
        .badge-green { background: var(--green-path); }
        .badge-purple { background: var(--purple-path); }

        .node-icon { font-size: 22px; margin-bottom: 6px; }
        .node-title { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 700; color: var(--text-main); line-height: 1.2; }
        .node-sub { font-size: 10px; color: var(--text-muted); margin-top: 4px; font-weight: 500; }

        /* Terminal Stream View */
        .terminal-container {
            display: none; height: 600px; flex-direction: column; background: #ffffff;
            border-radius: 16px; border: 1px solid var(--border-color); overflow: hidden;
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.02);
        }

        .terminal-header {
            padding: 14px 20px; background: #f8fafc; border-bottom: 1px solid var(--border-color);
            display: flex; align-items: center; justify-content: space-between;
        }

        .terminal-window {
            flex-grow: 1; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 13px;
            padding: 16px; display: flex; flex-direction: column; gap: 6px; background: #f8fafc;
        }

        .log-row { display: flex; gap: 14px; padding: 6px 10px; border-radius: 6px; word-break: break-all; border-bottom: 1px solid #edf2f7; }
        .log-row:hover { background: #edf2f7; }
        .log-ts { color: var(--text-muted); flex-shrink: 0; font-size: 12px; }
        .log-msg { color: #1e293b; }
        .highlight-cache { color: var(--green-path); font-weight: 600; }
        .highlight-error { color: var(--pink-path); font-weight: 600; }
        .highlight-download { color: var(--cyan-path); font-weight: 600; }

        /* Modal Inspector - Clean White Theme */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(8px); display: none; align-items: center; justify-content: center; z-index: 100;
        }

        .modal-card {
            width: 540px; background: #ffffff; border: 1px solid var(--border-color); border-radius: 20px;
            padding: 24px; box-shadow: 0 20px 50px rgba(15, 23, 42, 0.2); display: flex; flex-direction: column; gap: 16px;
        }

        .modal-header { display: flex; align-items: center; justify-content: space-between; }
        .modal-title { font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 800; color: var(--text-main); }
        .modal-close { cursor: pointer; color: var(--text-muted); font-size: 18px; }
        .modal-close:hover { color: var(--text-main); }

        .modal-code {
            background: #0f172a; padding: 16px; border-radius: 12px; border: 1px solid #1e293b;
            font-family: 'Fira Code', monospace; font-size: 12px; color: #38bdf8; line-height: 1.6;
        }

        .search-box {
            background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
            padding: 6px 12px; color: var(--text-main); font-size: 13px; outline: none; width: 220px;
        }

        @media (max-width: 900px) {
            .iso-map-wrapper { height: 500px; }
            .iso-map-viewport { transform: scale(0.65) rotateX(24deg) rotateZ(-12deg); }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Top Navigation -->
        <nav class="navbar">
            <div class="brand">
                <div class="brand-icon">
                    <i class="fa-brands fa-tiktok"></i>
                </div>
                <div class="brand-text">
                    <h1>ScrollSaver Process Map</h1>
                    <p>Isometric System Workflow Architecture & Operations</p>
                </div>
            </div>
            <div class="nav-controls">
                <button class="view-btn active" id="btn-view-map" onclick="switchView('map')">
                    <i class="fa-solid fa-diagram-project"></i> Process Map
                </button>
                <button class="view-btn" id="btn-view-terminal" onclick="switchView('terminal')">
                    <i class="fa-solid fa-terminal"></i> Terminal Logs
                </button>
            </div>
        </nav>

        <!-- Live Metrics Bar -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Uptime</h3>
                    <div class="metric-value" id="stat-uptime">0s</div>
                </div>
                <div class="metric-icon" style="color: var(--cyan-path);">
                    <i class="fa-solid fa-clock"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Total Requests</h3>
                    <div class="metric-value" id="stat-logs">0</div>
                </div>
                <div class="metric-icon" style="color: var(--pink-path);">
                    <i class="fa-solid fa-bolt"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Cache Hits</h3>
                    <div class="metric-value" id="stat-cache">0</div>
                </div>
                <div class="metric-icon" style="color: var(--green-path);">
                    <i class="fa-solid fa-database"></i>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Active Engines</h3>
                    <div class="metric-value">3 / 3</div>
                </div>
                <div class="metric-icon" style="color: var(--purple-path);">
                    <i class="fa-solid fa-microchip"></i>
                </div>
            </div>
        </div>

        <!-- Main Workspace -->
        <div class="main-section">
            <div class="section-header">
                <div class="section-title">
                    <i class="fa-solid fa-route"></i>
                    <span id="workspace-title">Interactive Process Workflow Diagram</span>
                </div>
                <div class="legend-bar" id="map-legend">
                    <div class="legend-item"><span class="legend-dot dot-pink"></span> Telegram User Flow</div>
                    <div class="legend-item"><span class="legend-dot dot-green"></span> Database Cache Fast-Path</div>
                    <div class="legend-item"><span class="legend-dot dot-purple"></span> Scraping & Downloader Pipeline</div>
                </div>
            </div>

            <!-- VIEW 1: ISOMETRIC PROCESS MAP -->
            <div class="iso-map-wrapper" id="view-map-wrapper">
                <div class="iso-map-viewport">
                    <!-- SVG Connecting Paths -->
                    <svg class="svg-canvas" viewBox="0 0 1100 600">
                        <!-- Pink Path: User Request -> Auth -> Router -> Dispatch -->
                        <path class="path-pink" d="M 80 120 L 260 120 L 440 120 L 980 120 L 980 480 L 800 480" />
                        <path class="path-pink animated-dash" d="M 80 120 L 260 120 L 440 120 L 980 120 L 980 480 L 800 480" />

                        <!-- Green Path: Database Cache Loop -->
                        <path class="path-green" d="M 440 120 L 440 280 L 620 280 L 800 280 L 800 480" />
                        <path class="path-green animated-dash" d="M 440 120 L 440 280 L 620 280 L 800 280 L 800 480" />

                        <!-- Purple Path: Extraction & Downloader Services -->
                        <path class="path-purple" d="M 440 120 L 260 480 L 440 480 L 620 480 L 800 480" />
                        <path class="path-purple animated-dash" d="M 440 120 L 260 480 L 440 480 L 620 480 L 800 480" />
                    </svg>

                    <!-- ISOMETRIC NODES -->
                    <!-- 1. Telegram Link Request -->
                    <div class="iso-node" style="top: 70px; left: 10px;" onclick="inspectNode('1')">
                        <span class="node-badge badge-pink">1</span>
                        <div class="node-icon" style="color: var(--pink-path);"><i class="fa-paper-plane"></i></div>
                        <div class="node-title">Link Request</div>
                        <div class="node-sub">@thescrollsaver_bot</div>
                    </div>

                    <!-- 2. Auth & Registration -->
                    <div class="iso-node" style="top: 70px; left: 190px;" onclick="inspectNode('2')">
                        <span class="node-badge badge-pink">2</span>
                        <div class="node-icon" style="color: var(--pink-path);"><i class="fa-user-check"></i></div>
                        <div class="node-title">Auth Check</div>
                        <div class="node-sub">users table register</div>
                    </div>

                    <!-- 3. URL Router -->
                    <div class="iso-node" style="top: 70px; left: 370px;" onclick="inspectNode('3')">
                        <span class="node-badge badge-pink">3</span>
                        <div class="node-icon" style="color: var(--pink-path);"><i class="fa-code-branch"></i></div>
                        <div class="node-title">URL Router</div>
                        <div class="node-sub">Validate TikTok URL</div>
                    </div>

                    <!-- 4. Database Cache Lookup -->
                    <div class="iso-node" style="top: 230px; left: 370px;" onclick="inspectNode('CACHE_LOOKUP')">
                        <span class="node-badge badge-green">A</span>
                        <div class="node-icon" style="color: var(--green-path);"><i class="fa-database"></i></div>
                        <div class="node-title">Cache Search</div>
                        <div class="node-sub">SELECT video_id</div>
                    </div>

                    <!-- 5. Cache Hit Fast Send -->
                    <div class="iso-node" style="top: 230px; left: 550px;" onclick="inspectNode('CACHE_HIT')">
                        <span class="node-badge badge-green">B</span>
                        <div class="node-icon" style="color: var(--green-path);"><i class="fa-bolt-lightning"></i></div>
                        <div class="node-title">Cache Hit (0.05s)</div>
                        <div class="node-sub">send_cached_media</div>
                    </div>

                    <!-- 6. TikWM API -->
                    <div class="iso-node" style="top: 430px; left: 190px;" onclick="inspectNode('TIKWM')">
                        <span class="node-badge badge-purple">7A</span>
                        <div class="node-icon" style="color: var(--purple-path);"><i class="fa-cloud-arrow-down"></i></div>
                        <div class="node-title">TikWM API</div>
                        <div class="node-sub">Primary Extractor</div>
                    </div>

                    <!-- 7. Fallback Web Scraper -->
                    <div class="iso-node" style="top: 430px; left: 370px;" onclick="inspectNode('SCRAPER')">
                        <span class="node-badge badge-purple">7B</span>
                        <div class="node-icon" style="color: var(--purple-path);"><i class="fa-globe"></i></div>
                        <div class="node-title">Page Rehydration</div>
                        <div class="node-sub">SIGI_STATE scraper</div>
                    </div>

                    <!-- 8. Musicaldown Engine -->
                    <div class="iso-node" style="top: 430px; left: 550px;" onclick="inspectNode('MUSICALDOWN')">
                        <span class="node-badge badge-purple">7C</span>
                        <div class="node-icon" style="color: var(--purple-path);"><i class="fa-download"></i></div>
                        <div class="node-title">Musicaldown</div>
                        <div class="node-sub">Secondary Fallback</div>
                    </div>

                    <!-- 9. Telegram Dispatcher -->
                    <div class="iso-node" style="top: 430px; left: 730px;" onclick="inspectNode('DISPATCH')">
                        <span class="node-badge badge-pink">4</span>
                        <div class="node-icon" style="color: var(--pink-path);"><i class="fa-share-from-square"></i></div>
                        <div class="node-title">Bot Dispatcher</div>
                        <div class="node-sub">send_video / photo</div>
                    </div>

                    <!-- 10. User Notification -->
                    <div class="iso-node" style="top: 230px; left: 730px;" onclick="inspectNode('NOTIFY')">
                        <span class="node-badge badge-pink">5</span>
                        <div class="node-icon" style="color: var(--pink-path);"><i class="fa-circle-check"></i></div>
                        <div class="node-title">Done & Clean</div>
                        <div class="node-sub">Delete status msg</div>
                    </div>
                </div>
            </div>

            <!-- VIEW 2: LIVE TERMINAL MONITOR -->
            <div class="terminal-container" id="view-terminal-wrapper">
                <div class="terminal-header">
                    <div class="section-title"><i class="fa-solid fa-terminal"></i> Activity Stream</div>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <input type="text" id="search-input" class="search-box" placeholder="Search logs...">
                        <button class="view-btn" onclick="fetchData()"><i class="fa-solid fa-rotate-right"></i></button>
                    </div>
                </div>
                <div class="terminal-window" id="terminal-body">
                    <div class="empty-logs">Connecting to log stream...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- NODE INSPECTOR MODAL -->
    <div class="modal-overlay" id="node-modal">
        <div class="modal-card">
            <div class="modal-header">
                <div class="modal-title" id="modal-node-title">Node Specification</div>
                <div class="modal-close" onclick="closeModal()"><i class="fa-solid fa-xmark"></i></div>
            </div>
            <p style="font-size: 13px; color: var(--text-muted);" id="modal-node-desc">Step details...</p>
            <div class="modal-code" id="modal-node-code"># Code implementation</div>
        </div>
    </div>

    <script>
        const NODE_SPECS = {
            '1': {
                title: 'Step 1: Telegram Link Request',
                desc: 'User sends a TikTok URL to @thescrollsaver_bot in Telegram chat.',
                code: 'async def tiktok_handler(client, message):\n    tiktok_url = message.text\n    log_activity(f"{user.id} - {tiktok_url}")'
            },
            '2': {
                title: 'Step 2: Auth & Registration Check',
                desc: 'Verifies user existence in SQL database (`users` table) and auto-registers new users.',
                code: 'async with databases.Database(DATABASE) as db:\n    result = await db.fetch_one("SELECT * FROM users WHERE user_id = :userid")\n    if not result:\n        await db.execute(users.insert(), values={...})'
            },
            '3': {
                title: 'Step 3: URL Router',
                desc: 'Validates TikTok URL format and routes to detail extraction pipeline.',
                code: 'video_id, author_id, author_username, video_url, images, cookies = \\\n    await get_video_detail(tiktok_url)'
            },
            'CACHE_LOOKUP': {
                title: 'Fast-Path: Database Cache Lookup',
                desc: 'Queries `videos` table to see if `video_id` has previously been uploaded to Telegram servers.',
                code: 'query = "SELECT * FROM videos WHERE video_id = :video_id AND author_id = :author_id"\nresult = await db.fetch_one(query=query, values=values)'
            },
            'CACHE_HIT': {
                title: 'Fast-Path: Instant Cache Re-Send (0.05s)',
                desc: 'Uses cached Telegram `file_id` to re-send media instantly without downloading video stream.',
                code: 'await client.send_cached_media(\n    chat_id=userid,\n    file_id=result.file_id,\n    caption=retext\n)'
            },
            'TIKWM': {
                title: 'Extraction 7A: TikWM API Lookup',
                desc: 'Primary extractor requesting TikWM API for clean HD video URL and slideshow photo list.',
                code: 'r = await ses.post("https://www.tikwm.com/api/", data={"url": url})\nres_json = r.json()\nvideo_url = res_json["data"]["play"]'
            },
            'SCRAPER': {
                title: 'Extraction 7B: Page Rehydration Scraping',
                desc: 'Direct HTTP scraper parsing JSON embedded tags (__UNIVERSAL_DATA_FOR_REHYDRATION__, SIGI_STATE).',
                code: 'infotag = parser.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__")\nitem = json.loads(infotag.text)["__DEFAULT_SCOPE__"]["webapp.video-detail"]'
            },
            'MUSICALDOWN': {
                title: 'Extraction 7C: Musicaldown Fallback Engine',
                desc: 'Backup downloader simulating user session on musicaldown.com to extract video stream.',
                code: 'res = await ses.post("https://musicaldown.com/download", data=data)\nurlVideo = parsing.find("a", class_="download").get("href")'
            },
            'DISPATCH': {
                title: 'Step 4: Telegram Media Dispatcher',
                desc: 'Sends downloaded HD MP4 video or photo media group to user chat.',
                code: 'result = await client.send_video(chat_id=userid, video=str(output), caption=retext)\n# Save file_id to database for caching'
            },
            'NOTIFY': {
                title: 'Step 5: Completion & Cleanup',
                desc: 'Deletes status notification message and unlinks temporary video/photo files from disk.',
                code: 'await status_msg.delete()\noutput.unlink(missing_ok=True)'
            }
        };

        function inspectNode(id) {
            const spec = NODE_SPECS[id];
            if (!spec) return;
            document.getElementById('modal-node-title').innerText = spec.title;
            document.getElementById('modal-node-desc').innerText = spec.desc;
            document.getElementById('modal-node-code').innerText = spec.code;
            document.getElementById('node-modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('node-modal').style.display = 'none';
        }

        function switchView(view) {
            if (view === 'map') {
                document.getElementById('view-map-wrapper').style.display = 'flex';
                document.getElementById('view-terminal-wrapper').style.display = 'none';
                document.getElementById('btn-view-map').classList.add('active');
                document.getElementById('btn-view-terminal').classList.remove('active');
                document.getElementById('workspace-title').innerText = 'Interactive Process Workflow Diagram';
            } else {
                document.getElementById('view-map-wrapper').style.display = 'none';
                document.getElementById('view-terminal-wrapper').style.display = 'flex';
                document.getElementById('btn-view-map').classList.remove('active');
                document.getElementById('btn-view-terminal').classList.add('active');
                document.getElementById('workspace-title').innerText = 'Real-Time Activity Terminal Stream';
            }
        }

        let cachedLogs = [];

        function formatUptime(sec) {
            const m = Math.floor(sec / 60);
            const s = sec % 60;
            return m > 0 ? `${m}m ${s}s` : `${s}s`;
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                document.getElementById('stat-uptime').innerText = formatUptime(stats.uptime || 0);
                document.getElementById('stat-logs').innerText = stats.total_logs || 0;
                document.getElementById('stat-cache').innerText = stats.cache_hits || 0;
            } catch (e) {}
        }

        async function fetchData() {
            try {
                const res = await fetch('/api/logs');
                cachedLogs = await res.json();
                renderLogs();
                fetchStats();
            } catch (e) {}
        }

        function renderLogs() {
            const container = document.getElementById('terminal-body');
            if (!cachedLogs || cachedLogs.length === 0) {
                container.innerHTML = '<div class="empty-logs">No activity logged yet.</div>';
                return;
            }

            container.innerHTML = cachedLogs.map(item => {
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
