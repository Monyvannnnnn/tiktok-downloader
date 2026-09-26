import json
import time
import base64
import asyncio
from config import PORT, BASE_DIR
from services.logger import recent_logs, log_activity

START_TIME = time.time()


def get_assets_map():
    assets = {}
    asset_dir = BASE_DIR.joinpath("asset")
    if asset_dir.exists():
        for f in asset_dir.glob("*"):
            if f.is_file():
                ext = f.suffix.lower()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                try:
                    b64 = base64.b64encode(f.read_bytes()).decode("utf-8")
                    assets[f.name] = f"data:{mime};base64,{b64}"
                except Exception:
                    pass
    return assets


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
            await writer.drain()
            return

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
            await writer.drain()
            return

        elif "/asset/" in req_str:
            try:
                parts = req_str.split("/asset/")
                if len(parts) > 1:
                    filename = parts[1].split(" ")[0].split("?")[0].strip()
                    asset_file = BASE_DIR.joinpath("asset", filename)
                    if asset_file.exists() and asset_file.is_file():
                        mime = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
                        body = asset_file.read_bytes()
                        header = (
                            "HTTP/1.1 200 OK\r\n"
                            f"Content-Type: {mime}\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(body)}\r\n\r\n"
                        ).encode("utf-8")
                        writer.write(header + body)
                        await writer.drain()
                        return
            except Exception:
                pass

        assets = get_assets_map()
        img_merch = assets.get("merchandising.png", "/asset/merchandising.png")
        img_10 = assets.get("10.png", "/asset/10.png")
        img_9 = assets.get("9.png", "/asset/9.png")
        img_11a = assets.get("11a.png", "/asset/11a.png")
        img_11b = assets.get("11b.png", "/asset/11b.png")
        img_recv = assets.get("receiving.png", "/asset/receiving.png")
        img_req = assets.get("images.jpg", "/asset/images.jpg")

        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScrollSaver - 3D Isometric Workflow with Assets</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #f1f5f9;
            --bg-card: #ffffff;
            --border-color: #cbd5e1;
            --pink-path: #e11d48;
            --green-path: #059669;
            --purple-path: #4f46e5;
            --cyan-path: #0284c7;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --shadow-3d: -5px 8px 0px #cbd5e1, -10px 16px 0px #94a3b8, 0 30px 60px rgba(15, 23, 42, 0.16);
            --shadow-hover: -8px 12px 0px #94a3b8, -14px 22px 0px #64748b, 0 45px 80px rgba(2, 132, 199, 0.25);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-body);
            background-image: 
                radial-gradient(at 15% 15%, rgba(79, 70, 229, 0.06) 0px, transparent 40%),
                radial-gradient(at 85% 85%, rgba(5, 150, 105, 0.06) 0px, transparent 40%),
                radial-gradient(at 50% 50%, rgba(225, 29, 72, 0.05) 0px, transparent 50%);
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
            border: 1.5px solid var(--border-color);
            padding: 16px 28px;
            border-radius: 20px;
            box-shadow: -4px 6px 0px #cbd5e1, 0 10px 30px rgba(0, 0, 0, 0.05);
        }

        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon {
            width: 46px; height: 46px; border-radius: 14px;
            background: linear-gradient(135deg, var(--pink-path), var(--purple-path));
            display: flex; align-items: center; justify-content: center;
            color: #fff; box-shadow: -2px 4px 0px #9f1239, 0 8px 18px rgba(225, 29, 72, 0.35);
        }

        .brand-text h1 {
            font-family: 'Outfit', sans-serif; font-size: 22px; font-weight: 800;
            color: var(--text-main); letter-spacing: -0.5px;
        }

        .brand-text p { font-size: 12px; color: var(--text-muted); font-weight: 500; }

        .nav-controls { display: flex; align-items: center; gap: 16px; }

        .view-btn {
            background: #ffffff; border: 1.5px solid var(--border-color);
            color: var(--text-main); padding: 9px 18px; border-radius: 12px;
            font-size: 13px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px;
            box-shadow: -2px 4px 0px #cbd5e1; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .view-btn.active, .view-btn:hover {
            background: var(--cyan-path); border-color: var(--cyan-path); color: #ffffff;
            box-shadow: -2px 4px 0px #0369a1, 0 8px 20px rgba(2, 132, 199, 0.3);
            transform: translateY(-2px);
        }

        /* Metrics Bar */
        .metrics-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;
        }

        .metric-card {
            background: var(--bg-card); border: 1.5px solid var(--border-color);
            border-radius: 18px; padding: 18px 22px; display: flex; align-items: center; justify-content: space-between;
            box-shadow: -3px 5px 0px #cbd5e1, 0 8px 20px rgba(15, 23, 42, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-3px); box-shadow: -4px 8px 0px #94a3b8, 0 12px 25px rgba(15, 23, 42, 0.1);
        }

        .metric-info h3 { font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-family: 'Outfit', sans-serif; font-size: 26px; font-weight: 800; color: var(--text-main); }
        .metric-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: #f8fafc; border: 1.5px solid var(--border-color); overflow: hidden; }

        /* Main Workspace Container */
        .main-section {
            background: var(--bg-card); border: 1.5px solid var(--border-color);
            border-radius: 24px; padding: 26px; position: relative; overflow: hidden;
            box-shadow: -6px 10px 0px #cbd5e1, 0 20px 40px rgba(15, 23, 42, 0.08);
        }

        .section-header {
            display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;
            padding-bottom: 16px; border-bottom: 1.5px solid var(--border-color);
        }

        .section-title {
            font-family: 'Outfit', sans-serif; font-size: 19px; font-weight: 800; color: var(--text-main);
            display: flex; align-items: center; gap: 10px;
        }

        /* Legend Bar */
        .legend-bar {
            display: flex; align-items: center; gap: 20px; flex-wrap: wrap; font-size: 13px; font-weight: 700; color: var(--text-muted);
        }

        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-dot { width: 14px; height: 14px; border-radius: 50%; display: inline-block; border: 2px solid #fff; }
        .dot-pink { background: var(--pink-path); box-shadow: 0 0 10px rgba(225, 29, 72, 0.4); }
        .dot-green { background: var(--green-path); box-shadow: 0 0 10px rgba(5, 150, 105, 0.4); }
        .dot-purple { background: var(--purple-path); box-shadow: 0 0 10px rgba(79, 70, 229, 0.4); }

        /* 3D ISOMETRIC CANVAS WRAPPER */
        .iso-map-wrapper {
            width: 100%; height: 740px; position: relative; border-radius: 20px;
            background: radial-gradient(circle at 50% 40%, #ffffff 0%, #f1f5f9 65%, #e2e8f0 100%);
            border: 2px solid var(--border-color); overflow: hidden; display: flex; align-items: center; justify-content: center;
            perspective: 1200px;
            box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.04);
        }

        .iso-map-viewport {
            width: 1100px; height: 620px; position: relative;
            transform: rotateX(42deg) rotateZ(-22deg) rotateY(8deg);
            transform-style: preserve-3d;
            transition: transform 0.15s ease-out;
        }

        /* SVG Paths */
        .svg-canvas {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;
            transform: translateZ(10px);
        }

        .path-pink { stroke: var(--pink-path); stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round; filter: drop-shadow(-3px 5px 6px rgba(225, 29, 72, 0.35)); }
        .path-green { stroke: var(--green-path); stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round; filter: drop-shadow(-3px 5px 6px rgba(5, 150, 105, 0.35)); }
        .path-purple { stroke: var(--purple-path); stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round; filter: drop-shadow(-3px 5px 6px rgba(79, 70, 229, 0.35)); }

        .animated-dash {
            stroke-dasharray: 14 14; animation: flow-dash 1.5s linear infinite;
        }

        @keyframes flow-dash {
            from { stroke-dashoffset: 56; }
            to { stroke-dashoffset: 0; }
        }

        /* TRUE 3D EXTRUDED NODE CARDS WITH ASSET IMAGES */
        .iso-node {
            position: absolute; width: 160px; height: 145px; padding: 12px; border-radius: 20px;
            background: #ffffff; border: 2px solid #cbd5e1;
            transform-style: preserve-3d;
            box-shadow: var(--shadow-3d);
            cursor: pointer; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            display: flex; flex-direction: column; align-items: center; text-align: center; justify-content: center;
        }

        .iso-node:hover {
            transform: translateZ(45px) scale(1.12);
            border-color: var(--cyan-path);
            box-shadow: var(--shadow-hover);
            z-index: 100;
        }

        .node-badge {
            position: absolute; top: -14px;
            width: 28px; height: 28px; border-radius: 50%; font-size: 11px; font-weight: 800;
            display: flex; align-items: center; justify-content: center; color: #ffffff;
            border: 2px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.25);
            transform: translateZ(35px);
        }

        .badge-pink { background: var(--pink-path); }
        .badge-green { background: var(--green-path); }
        .badge-purple { background: var(--purple-path); }

        .node-asset-img {
            width: 52px; height: 52px; object-fit: contain;
            margin-bottom: 6px; transform: translateZ(30px);
            filter: drop-shadow(0 6px 12px rgba(0,0,0,0.15));
            transition: transform 0.3s ease;
        }

        .iso-node:hover .node-asset-img {
            transform: translateZ(50px) scale(1.15);
        }

        .node-title {
            font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 800; color: var(--text-main); line-height: 1.25;
            transform: translateZ(20px);
        }

        .node-sub {
            font-size: 10px; color: var(--text-muted); margin-top: 3px; font-weight: 600;
            transform: translateZ(15px);
        }

        .fallback-svg {
            width: 32px; height: 32px; fill: var(--purple-path); display: none; margin-bottom: 6px; transform: translateZ(30px);
        }

        /* Terminal Stream View */
        .terminal-container {
            display: none; height: 600px; flex-direction: column; background: #ffffff;
            border-radius: 18px; border: 1.5px solid var(--border-color); overflow: hidden;
            box-shadow: -4px 8px 0px #cbd5e1;
        }

        .terminal-header {
            padding: 14px 20px; background: #f8fafc; border-bottom: 1.5px solid var(--border-color);
            display: flex; align-items: center; justify-content: space-between;
        }

        .terminal-window {
            flex-grow: 1; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 13px;
            padding: 16px; display: flex; flex-direction: column; gap: 6px; background: #f8fafc;
        }

        .log-row { display: flex; gap: 14px; padding: 6px 10px; border-radius: 6px; word-break: break-all; border-bottom: 1px solid #e2e8f0; }
        .log-row:hover { background: #e2e8f0; }
        .log-ts { color: var(--text-muted); flex-shrink: 0; font-size: 12px; }
        .log-msg { color: #1e293b; }
        .highlight-cache { color: var(--green-path); font-weight: 700; }
        .highlight-error { color: var(--pink-path); font-weight: 700; }
        .highlight-download { color: var(--cyan-path); font-weight: 700; }

        /* Modal Inspector */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(8px); display: none; align-items: center; justify-content: center; z-index: 200;
        }

        .modal-card {
            width: 560px; background: #ffffff; border: 2px solid var(--cyan-path); border-radius: 22px;
            padding: 26px; box-shadow: -8px 16px 0px rgba(2, 132, 199, 0.2), 0 30px 60px rgba(15, 23, 42, 0.25); display: flex; flex-direction: column; gap: 16px;
        }

        .modal-header { display: flex; align-items: center; justify-content: space-between; }
        .modal-title { font-family: 'Outfit', sans-serif; font-size: 19px; font-weight: 800; color: var(--text-main); }
        .modal-close { cursor: pointer; color: var(--text-muted); font-size: 20px; font-weight: 800; }
        .modal-close:hover { color: var(--text-main); }

        .modal-code {
            background: #0f172a; padding: 18px; border-radius: 14px; border: 1px solid #1e293b;
            font-family: 'Fira Code', monospace; font-size: 12px; color: #38bdf8; line-height: 1.6;
        }

        .search-box {
            background: #ffffff; border: 1.5px solid var(--border-color); border-radius: 10px;
            padding: 7px 14px; color: var(--text-main); font-size: 13px; outline: none; width: 220px;
        }

        @media (max-width: 900px) {
            .iso-map-wrapper { height: 520px; }
            .iso-map-viewport { transform: scale(0.62) rotateX(42deg) rotateZ(-22deg) rotateY(8deg); }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Top Navigation -->
        <nav class="navbar">
            <div class="brand">
                <div class="brand-icon">
                    <img src="__IMG_MERCH__" style="width: 32px; height: 32px; object-fit: contain;">
                </div>
                <div class="brand-text">
                    <h1>ScrollSaver 3D Process Map</h1>
                    <p>Isometric Workflow Diagram with Asset Images</p>
                </div>
            </div>
            <div class="nav-controls">
                <button class="view-btn active" id="btn-view-map" onclick="switchView('map')">
                    3D Process Map
                </button>
                <button class="view-btn" id="btn-view-terminal" onclick="switchView('terminal')">
                    Terminal Stream
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
                <div class="metric-icon">
                    <img src="__IMG_10__" style="width: 32px; height: 32px; object-fit: contain;">
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Total Requests</h3>
                    <div class="metric-value" id="stat-logs">0</div>
                </div>
                <div class="metric-icon">
                    <img src="__IMG_9__" style="width: 32px; height: 32px; object-fit: contain;">
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Cache Hits</h3>
                    <div class="metric-value" id="stat-cache">0</div>
                </div>
                <div class="metric-icon">
                    <img src="__IMG_11A__" style="width: 32px; height: 32px; object-fit: contain;">
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-info">
                    <h3>Active Engines</h3>
                    <div class="metric-value">3 / 3</div>
                </div>
                <div class="metric-icon">
                    <img src="__IMG_RECV__" style="width: 32px; height: 32px; object-fit: contain;">
                </div>
            </div>
        </div>

        <!-- Main Workspace -->
        <div class="main-section">
            <div class="section-header">
                <div class="section-title">
                    <img src="__IMG_11B__" style="width: 28px; height: 28px; object-fit: contain; vertical-align: middle;">
                    <span id="workspace-title">Interactive 3D Process Map & Asset Pipeline</span>
                </div>
                <div class="legend-bar" id="map-legend">
                    <div class="legend-item"><span class="legend-dot dot-pink"></span> Telegram User Flow</div>
                    <div class="legend-item"><span class="legend-dot dot-green"></span> Database Cache Fast-Path</div>
                    <div class="legend-item"><span class="legend-dot dot-purple"></span> Scraping & Downloader Pipeline</div>
                </div>
            </div>

            <!-- VIEW 1: 3D ISOMETRIC PROCESS MAP -->
            <div class="iso-map-wrapper" id="view-map-wrapper">
                <div class="iso-map-viewport" id="iso-viewport">
                    <!-- SVG Connecting Paths -->
                    <svg class="svg-canvas" viewBox="0 0 1100 600">
                        <!-- Pink Path: User Request -> Auth -> Router -> Dispatch Loop -->
                        <path class="path-pink" d="M 115 115 L 305 115 L 495 115 L 1010 115 L 1010 315 L 875 315" />
                        <path class="path-pink animated-dash" d="M 115 115 L 305 115 L 495 115 L 1010 115 L 1010 315 L 875 315" />

                        <!-- Green Path: Database Cache Loop -->
                        <path class="path-green" d="M 495 115 L 495 315 L 685 315 L 875 315" />
                        <path class="path-green animated-dash" d="M 495 115 L 495 315 L 685 315 L 875 315" />

                        <!-- Purple Path: Extraction & Downloader Pipeline -->
                        <path class="path-purple" d="M 495 115 L 305 505 L 495 505 L 685 505 L 875 505 L 875 315" />
                        <path class="path-purple animated-dash" d="M 495 115 L 305 505 L 495 505 L 685 505 L 875 505 L 875 315" />
                    </svg>

                    <!-- ISOMETRIC 3D EXTRUDED NODES WITH EMBEDDED BASE64 ASSET IMAGES -->
                    <!-- 1. Telegram Link Request -->
                    <div class="iso-node" style="top: 50px; left: 40px;" onclick="inspectNode('1')">
                        <span class="node-badge badge-pink">1</span>
                        <img src="__IMG_REQ__" class="node-asset-img" alt="Request" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                        <div class="node-title">Link Request</div>
                        <div class="node-sub">@thescrollsaver_bot</div>
                    </div>

                    <!-- 2. Auth & Registration -->
                    <div class="iso-node" style="top: 50px; left: 230px;" onclick="inspectNode('2')">
                        <span class="node-badge badge-pink">2</span>
                        <img src="__IMG_MERCH__" class="node-asset-img" alt="Auth" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
                        <div class="node-title">Auth Check</div>
                        <div class="node-sub">users table register</div>
                    </div>

                    <!-- 3. URL Router -->
                    <div class="iso-node" style="top: 50px; left: 420px;" onclick="inspectNode('3')">
                        <span class="node-badge badge-pink">3</span>
                        <img src="__IMG_RECV__" class="node-asset-img" alt="Router" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M17 7h-4v2h4c1.65 0 3 1.35 3 3s-1.35 3-3 3h-4v2h4c2.76 0 5-2.24 5-5s-2.24-5-5-5zm-6 8H7c-1.65 0-3-1.35-3-3s1.35-3 3-3h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-2zm-3-4h8v2H8z"/></svg>
                        <div class="node-title">URL Router</div>
                        <div class="node-sub">Validate TikTok URL</div>
                    </div>

                    <!-- 4. Database Cache Search -->
                    <div class="iso-node" style="top: 250px; left: 420px;" onclick="inspectNode('CACHE_LOOKUP')">
                        <span class="node-badge badge-green">A</span>
                        <img src="__IMG_9__" class="node-asset-img" alt="Cache" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M12 3C7.58 3 4 4.79 4 7v10c0 2.21 3.58 4 8 4s8-1.79 8-4V7c0-2.21-3.58-4-8-4zm0 2c3.87 0 6 1.3 6 2s-2.13 2-6 2-6-1.3-6-2 2.13-2 6-2z"/></svg>
                        <div class="node-title">Cache Search</div>
                        <div class="node-sub">SELECT video_id</div>
                    </div>

                    <!-- 5. Cache Hit Fast Send -->
                    <div class="iso-node" style="top: 250px; left: 610px;" onclick="inspectNode('CACHE_HIT')">
                        <span class="node-badge badge-green">B</span>
                        <img src="__IMG_10__" class="node-asset-img" alt="Fast Hit" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M7 2v11h3v9l7-12h-4l4-8z"/></svg>
                        <div class="node-title">Cache Hit (0.05s)</div>
                        <div class="node-sub">send_cached_media</div>
                    </div>

                    <!-- 6. Done & Clean -->
                    <div class="iso-node" style="top: 250px; left: 800px;" onclick="inspectNode('NOTIFY')">
                        <span class="node-badge badge-green">5</span>
                        <img src="__IMG_11A__" class="node-asset-img" alt="Done" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                        <div class="node-title">Done & Clean</div>
                        <div class="node-sub">Delete status msg</div>
                    </div>

                    <!-- 7. TikWM API -->
                    <div class="iso-node" style="top: 440px; left: 230px;" onclick="inspectNode('TIKWM')">
                        <span class="node-badge badge-purple">7A</span>
                        <img src="__IMG_11B__" class="node-asset-img" alt="TikWM" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
                        <div class="node-title">TikWM API</div>
                        <div class="node-sub">Primary Extractor</div>
                    </div>

                    <!-- 8. Page Rehydration Scraper -->
                    <div class="iso-node" style="top: 440px; left: 420px;" onclick="inspectNode('SCRAPER')">
                        <span class="node-badge badge-purple">7B</span>
                        <img src="__IMG_9__" class="node-asset-img" alt="Scraper" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        <div class="node-title">Page Rehydration</div>
                        <div class="node-sub">SIGI_STATE scraper</div>
                    </div>

                    <!-- 9. Musicaldown Engine -->
                    <div class="iso-node" style="top: 440px; left: 610px;" onclick="inspectNode('MUSICALDOWN')">
                        <span class="node-badge badge-purple">7C</span>
                        <img src="__IMG_10__" class="node-asset-img" alt="Musicaldown" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
                        <div class="node-title">Musicaldown</div>
                        <div class="node-sub">Secondary Fallback</div>
                    </div>

                    <!-- 10. Bot Dispatcher -->
                    <div class="iso-node" style="top: 440px; left: 800px;" onclick="inspectNode('DISPATCH')">
                        <span class="node-badge badge-purple">4</span>
                        <img src="__IMG_RECV__" class="node-asset-img" alt="Dispatcher" onerror="handleImgError(this)">
                        <svg class="fallback-svg" viewBox="0 0 24 24"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/></svg>
                        <div class="node-title">Bot Dispatcher</div>
                        <div class="node-sub">send_video / photo</div>
                    </div>
                </div>
            </div>

            <!-- VIEW 2: LIVE TERMINAL MONITOR -->
            <div class="terminal-container" id="view-terminal-wrapper">
                <div class="terminal-header">
                    <div class="section-title">Activity Stream</div>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <input type="text" id="search-input" class="search-box" placeholder="Search logs...">
                        <button class="view-btn" onclick="fetchData()">Refresh</button>
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
                <div class="modal-close" onclick="closeModal()">&times;</div>
            </div>
            <p style="font-size: 13px; color: var(--text-muted);" id="modal-node-desc">Step details...</p>
            <div class="modal-code" id="modal-node-code"># Code implementation</div>
        </div>
    </div>

    <script>
        function handleImgError(imgEl) {
            imgEl.style.display = 'none';
            const nextSvg = imgEl.nextElementSibling;
            if (nextSvg && nextSvg.classList.contains('fallback-svg')) {
                nextSvg.style.display = 'block';
            }
        }

        // 3D Mouse Parallax Effect
        const wrapper = document.getElementById('view-map-wrapper');
        const viewport = document.getElementById('iso-viewport');

        wrapper.addEventListener('mousemove', (e) => {
            const rect = wrapper.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            
            const rotX = 42 + (y * -14);
            const rotZ = -22 + (x * 14);
            const rotY = 8 + (x * 10);

            viewport.style.transform = `rotateX(${rotX}deg) rotateZ(${rotZ}deg) rotateY(${rotY}deg)`;
        });

        wrapper.addEventListener('mouseleave', () => {
            viewport.style.transform = 'rotateX(42deg) rotateZ(-22deg) rotateY(8deg)';
        });

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
                document.getElementById('workspace-title').innerText = 'Interactive 3D Process Map & Asset Pipeline';
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
</html>""".replace("__IMG_MERCH__", img_merch).replace("__IMG_10__", img_10).replace("__IMG_9__", img_9).replace("__IMG_11A__", img_11a).replace("__IMG_11B__", img_11b).replace("__IMG_RECV__", img_recv).replace("__IMG_REQ__", img_req)

        body = html_template.encode("utf-8")
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
